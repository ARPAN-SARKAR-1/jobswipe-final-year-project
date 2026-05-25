import hashlib
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from secrets import token_urlsafe
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.company import Company
from app.models.company_claim_request import CompanyClaimRequest
from app.models.company_member import CompanyMember
from app.models.enums import (
    CompanyClaimStatus,
    CompanyMemberRole,
    CompanyVerificationStatus,
    RecruiterVerificationStatus,
    RiskLevel,
    UserRole,
)
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User
from app.services.email_service import email_service
from app.services.notifications import create_notification, notify_admins

logger = logging.getLogger(__name__)

RESERVED_COMPANY_NAMES = [
    "TCS",
    "Tata Consultancy Services",
    "Infosys",
    "Wipro",
    "Accenture",
    "Capgemini",
    "Cognizant",
    "IBM",
    "Microsoft",
    "Google",
    "Amazon",
    "Deloitte",
    "HCL",
    "Tech Mahindra",
]

GENERIC_BRAND_SUFFIXES = ["careers", "career", "hiring", "jobs", "job", "recruitment", "campus", "hr"]


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_company_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def normalize_domain(value: str) -> str:
    text = value.strip().lower()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company domain is required.")
    parsed = urlparse(text if "://" in text else f"https://{text}")
    domain = (parsed.netloc or parsed.path).split("/", 1)[0].split(":", 1)[0].lstrip("www.")
    if "." not in domain or any(char.isspace() for char in domain):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company domain must be valid.")
    return domain


def email_domain(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Official email must be valid.")
    return email.rsplit("@", 1)[-1].lstrip("www.")


def ensure_domain_matches(official_email: str, requested_domain: str) -> None:
    if email_domain(official_email) != normalize_domain(requested_domain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Official email domain must match the company domain.",
        )


def reserved_brand_match(company_name: str) -> tuple[str | None, float]:
    normalized = normalize_company_name(company_name)
    cleaned = normalized
    for suffix in GENERIC_BRAND_SUFFIXES:
        cleaned = re.sub(f"{suffix}$", "", cleaned)
    best_name = None
    best_score = 0.0
    for reserved in RESERVED_COMPANY_NAMES:
        target = normalize_company_name(reserved)
        score = max(
            SequenceMatcher(None, normalized, target).ratio(),
            SequenceMatcher(None, cleaned, target).ratio(),
        )
        if normalized.startswith(target) or target.startswith(cleaned):
            score = max(score, 0.92)
        if score > best_score:
            best_name = reserved
            best_score = score
    return (best_name, best_score) if best_score >= 0.82 else (None, best_score)


def assess_company_claim_risk(company_name: str, domain: str, official_email: str) -> tuple[int, str, list[str]]:
    score = 0
    reasons: list[str] = []
    match_name, match_score = reserved_brand_match(company_name)
    if match_name:
        score += 70 if match_score >= 0.9 else 50
        reasons.append(f"Company name is reserved or similar to {match_name}.")
    if email_domain(official_email) != normalize_domain(domain):
        score += 40
        reasons.append("Official email domain does not match requested company domain.")
    if score >= 61:
        return min(score, 100), RiskLevel.HIGH.value, reasons
    if score >= 31:
        return score, RiskLevel.MEDIUM.value, reasons
    return score, RiskLevel.LOW.value, reasons


def hash_verification_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_claim_token() -> tuple[str, str, datetime]:
    token = token_urlsafe(32)
    return token, hash_verification_token(token), utc_now_naive() + timedelta(hours=24)


def log_company_claim_token(claim: CompanyClaimRequest, token: str) -> None:
    verify_url = f"{settings.frontend_url.split(',')[0].rstrip('/')}/recruiter/company?claimToken={token}"
    email_service.send_company_claim_verification(claim.official_email, verify_url, token, claim.id)


def find_company_by_normalized_name(db: Session, company_name: str) -> Company | None:
    target = normalize_company_name(company_name)
    companies = db.scalars(select(Company)).all()
    for company in companies:
        if normalize_company_name(company.company_name) == target:
            return company
    return None


def has_verified_company_owner(db: Session, company_id: int) -> bool:
    count = db.scalar(
        select(func.count(CompanyMember.id))
        .where(CompanyMember.company_id == company_id)
        .where(CompanyMember.company_role == CompanyMemberRole.COMPANY_OWNER.value)
        .where(CompanyMember.verification_status == RecruiterVerificationStatus.VERIFIED.value)
    )
    return bool(count)


def get_company_member(db: Session, company_id: int, user_id: int) -> CompanyMember | None:
    return db.scalar(
        select(CompanyMember).where(CompanyMember.company_id == company_id).where(CompanyMember.user_id == user_id)
    )


def ensure_company_member(
    db: Session,
    company_id: int,
    user_id: int,
    company_role: str = CompanyMemberRole.COMPANY_RECRUITER.value,
    verification_status: str = RecruiterVerificationStatus.PENDING.value,
    note: str | None = None,
) -> CompanyMember:
    member = get_company_member(db, company_id, user_id)
    if member is None:
        member = CompanyMember(
            company_id=company_id,
            user_id=user_id,
            company_role=company_role,
            verification_status=verification_status,
            requested_at=utc_now_naive(),
            note=note,
        )
        db.add(member)
        db.flush()
        return member
    if member.verification_status == RecruiterVerificationStatus.REJECTED.value:
        member.verification_status = verification_status
        member.note = note
        member.requested_at = utc_now_naive()
    return member


def user_can_manage_company_members(db: Session, user: User, company_id: int) -> CompanyMember | None:
    if user.role in {UserRole.OWNER.value, UserRole.ADMIN.value}:
        return None
    member = get_company_member(db, company_id, user.id)
    if (
        member
        and member.verification_status == RecruiterVerificationStatus.VERIFIED.value
        and member.company_role in {CompanyMemberRole.COMPANY_OWNER.value, CompanyMemberRole.COMPANY_ADMIN.value}
    ):
        return member
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot manage this company.")


def ensure_company_owner_or_platform_admin(db: Session, user: User, company_id: int) -> CompanyMember | None:
    if user.role in {UserRole.OWNER.value, UserRole.ADMIN.value}:
        return None
    member = get_company_member(db, company_id, user.id)
    if (
        member
        and member.verification_status == RecruiterVerificationStatus.VERIFIED.value
        and member.company_role == CompanyMemberRole.COMPANY_OWNER.value
    ):
        return member
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the company owner can perform this action.")


def approve_company_member(db: Session, member: CompanyMember, actor: User, note: str | None = None) -> CompanyMember:
    member.verification_status = RecruiterVerificationStatus.VERIFIED.value
    member.verified_at = utc_now_naive()
    member.verified_by_user_id = actor.id
    member.note = note or member.note

    profile = db.scalar(select(RecruiterProfile).where(RecruiterProfile.user_id == member.user_id))
    user = db.get(User, member.user_id)
    if profile is None and user is not None:
        profile = RecruiterProfile(user_id=member.user_id, company_id=member.company_id, official_email=user.email)
        db.add(profile)
    if profile is not None:
        profile.company_id = member.company_id
        profile.recruiter_verification_status = RecruiterVerificationStatus.VERIFIED.value
        profile.verified_at = member.verified_at
        profile.verified_by_admin_id = actor.id
        if user and not profile.official_email:
            profile.official_email = user.email
    create_notification(
        db,
        member.user_id,
        "Company membership approved",
        "Your company membership has been approved.",
        "COMPANY_MEMBER_APPROVED",
        "/recruiter/company",
    )
    return member


def reject_company_member(db: Session, member: CompanyMember, actor: User, note: str | None = None) -> CompanyMember:
    if member.company_role == CompanyMemberRole.COMPANY_OWNER.value and actor.role not in {UserRole.OWNER.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company owner cannot be rejected by lower company admins.")
    member.verification_status = RecruiterVerificationStatus.REJECTED.value
    member.verified_at = None
    member.verified_by_user_id = actor.id
    member.note = note
    create_notification(
        db,
        member.user_id,
        "Company membership rejected",
        note or "Your company membership request was rejected.",
        "COMPANY_MEMBER_REJECTED",
        "/recruiter/company",
    )
    return member


def finalize_claim_as_verified(db: Session, claim: CompanyClaimRequest, reviewer: User | None = None) -> CompanyClaimRequest:
    company = claim.company
    requester = claim.requester
    if company is None or requester is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company claim not found.")

    company.verification_status = CompanyVerificationStatus.VERIFIED.value
    company.official_email_domain = claim.requested_domain
    company.verified_at = utc_now_naive()
    company.verified_by_admin_id = reviewer.id if reviewer else None
    company.verification_note = "Verified through official domain claim."
    claim.claim_status = CompanyClaimStatus.VERIFIED.value
    claim.reviewed_by_admin_id = reviewer.id if reviewer else claim.reviewed_by_admin_id
    claim.admin_note = reviewer and (claim.admin_note or "Approved after company claim review.") or claim.admin_note

    owner_role = CompanyMemberRole.COMPANY_OWNER.value if not has_verified_company_owner(db, company.id) else CompanyMemberRole.COMPANY_RECRUITER.value
    member = ensure_company_member(
        db,
        company.id,
        requester.id,
        owner_role,
        RecruiterVerificationStatus.VERIFIED.value,
        "Verified through official company domain claim.",
    )
    member.company_role = owner_role
    member.verification_status = RecruiterVerificationStatus.VERIFIED.value
    member.verified_at = utc_now_naive()
    member.verified_by_user_id = reviewer.id if reviewer else requester.id

    profile = db.scalar(select(RecruiterProfile).where(RecruiterProfile.user_id == requester.id))
    if profile is None:
        profile = RecruiterProfile(user_id=requester.id, company_id=company.id, official_email=claim.official_email)
        db.add(profile)
    profile.company_id = company.id
    profile.official_email = claim.official_email
    profile.recruiter_verification_status = RecruiterVerificationStatus.VERIFIED.value
    profile.verified_at = utc_now_naive()
    profile.verified_by_admin_id = reviewer.id if reviewer else requester.id

    create_notification(
        db,
        requester.id,
        "Company claim verified",
        f"{company.company_name} has been verified and linked to your recruiter account.",
        "COMPANY_CLAIM_VERIFIED",
        "/recruiter/company",
    )
    return claim


def claim_risk_reasons_json(reasons: list[str]) -> str:
    return json.dumps(reasons)


def notify_company_managers(db: Session, company_id: int, title: str, message: str, notification_type: str) -> None:
    manager_ids = db.scalars(
        select(CompanyMember.user_id)
        .where(CompanyMember.company_id == company_id)
        .where(CompanyMember.verification_status == RecruiterVerificationStatus.VERIFIED.value)
        .where(CompanyMember.company_role.in_([CompanyMemberRole.COMPANY_OWNER.value, CompanyMemberRole.COMPANY_ADMIN.value]))
    ).all()
    if not manager_ids:
        notify_admins(db, title, message, notification_type, "/admin/dashboard")
        return
    for user_id in manager_ids:
        create_notification(db, user_id, title, message, notification_type, "/recruiter/company")
