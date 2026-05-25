from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_current_user, require_roles
from app.models.application import Application
from app.models.company import Company
from app.models.company_claim_request import CompanyClaimRequest
from app.models.company_member import CompanyMember
from app.models.company_review import CompanyReview
from app.models.enums import (
    AccountStatus,
    CompanyClaimStatus,
    CompanyMemberRole,
    CompanyVerificationStatus,
    JobModerationStatus,
    RecruiterVerificationStatus,
    ReviewModerationStatus,
    UserRole,
)
from app.models.job import Job
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User
from app.schemas.company import (
    CompanyClaimCreate,
    CompanyClaimRead,
    CompanyClaimVerifyRead,
    CompanyDetailRead,
    CompanyJoinRequestRead,
    CompanyMemberActionRequest,
    CompanyMemberRoleUpdate,
    CompanyRead,
    CompanyRecruiterRead,
    CompanyReviewCreate,
    CompanyReviewRead,
    CompanyReviewSummaryRead,
)
from app.schemas.job import JobRead
from app.services.company_claims import (
    approve_company_member,
    assess_company_claim_risk,
    claim_risk_reasons_json,
    create_claim_token,
    email_domain,
    ensure_company_member,
    ensure_company_owner_or_platform_admin,
    ensure_domain_matches,
    finalize_claim_as_verified,
    find_company_by_normalized_name,
    get_company_member,
    hash_verification_token,
    log_company_claim_token,
    notify_company_managers,
    reject_company_member,
    user_can_manage_company_members,
)
from app.services.company_reviews import company_review_summary, recalculate_company_rating
from app.services.notifications import notify_admins
from app.services.review_moderation import contains_abusive_language
from app.utils.pagination import LimitQuery, PageQuery, pagination_offset

router = APIRouter(prefix="/companies", tags=["Companies"])


def public_jobs_statement(company_id: int):
    return (
        select(Job)
        .join(RecruiterProfile, Job.recruiter_id == RecruiterProfile.user_id)
        .join(User, Job.recruiter_id == User.id)
        .where(Job.company_id == company_id)
        .where(Job.company_id == RecruiterProfile.company_id)
        .where(Job.is_active.is_(True))
        .where(Job.deadline >= date.today())
        .where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
        .where(RecruiterProfile.recruiter_verification_status == RecruiterVerificationStatus.VERIFIED.value)
        .where(User.account_status == AccountStatus.ACTIVE.value)
    )


def company_response(db: Session, company: Company) -> CompanyRead:
    active_jobs_count = 0
    if company.verification_status == CompanyVerificationStatus.VERIFIED.value:
        active_jobs_count = db.scalar(select(func.count()).select_from(public_jobs_statement(company.id).subquery())) or 0
    recruiter_count = db.scalar(select(func.count(RecruiterProfile.id)).where(RecruiterProfile.company_id == company.id)) or 0
    return CompanyRead(
        id=company.id,
        company_name=company.company_name,
        company_logo_url=company.company_logo_url,
        company_type=company.company_type,
        industry=company.industry,
        website=company.website,
        official_email_domain=company.official_email_domain,
        description=company.description,
        headquarters_location=company.headquarters_location,
        founded_year=company.founded_year,
        company_size=company.company_size,
        registration_number=company.registration_number,
        verification_status=company.verification_status,
        verification_note=company.verification_note,
        verified_by_admin_id=company.verified_by_admin_id,
        verified_at=company.verified_at,
        average_rating=company.average_rating,
        total_reviews=company.total_reviews,
        active_jobs_count=active_jobs_count,
        recruiter_count=recruiter_count,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def review_response(review: CompanyReview) -> CompanyReviewRead:
    return CompanyReviewRead(
        id=review.id,
        company_id=review.company_id,
        job_seeker_id=review.job_seeker_id,
        application_id=review.application_id,
        rating=review.rating,
        overall_rating=review.overall_rating,
        work_culture_rating=review.work_culture_rating,
        interview_process_rating=review.interview_process_rating,
        salary_transparency_rating=review.salary_transparency_rating,
        growth_opportunity_rating=review.growth_opportunity_rating,
        review_title=review.review_title,
        review_text=review.review_text,
        pros=review.pros,
        cons=review.cons,
        is_anonymous=review.is_anonymous,
        is_visible=review.is_visible,
        moderation_status=review.moderation_status,
        reviewer_name=None if review.is_anonymous else (review.job_seeker.name if review.job_seeker else None),
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def claim_response(claim: CompanyClaimRequest) -> CompanyClaimRead:
    return CompanyClaimRead(
        id=claim.id,
        company_id=claim.company_id,
        requested_company_name=claim.requested_company_name,
        requested_domain=claim.requested_domain,
        requester_user_id=claim.requester_user_id,
        official_email=claim.official_email,
        claim_status=claim.claim_status,
        email_verified_at=claim.email_verified_at,
        reviewed_by_admin_id=claim.reviewed_by_admin_id,
        admin_note=claim.admin_note,
        risk_score=claim.risk_score,
        risk_level=claim.risk_level,
        requires_admin_review=claim.requires_admin_review,
        risk_reasons=claim.risk_reasons,
        company_name=claim.company.company_name if claim.company else None,
        requester_name=claim.requester.name if claim.requester else None,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
    )


def member_response(member: CompanyMember) -> CompanyJoinRequestRead:
    return CompanyJoinRequestRead(
        id=member.id,
        company_id=member.company_id,
        user_id=member.user_id,
        company_role=member.company_role,
        verification_status=member.verification_status,
        requested_at=member.requested_at,
        verified_at=member.verified_at,
        verified_by_user_id=member.verified_by_user_id,
        note=member.note,
        user_name=member.user.name if member.user else None,
        user_email=member.user.email if member.user else None,
        company_name=member.company.company_name if member.company else None,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


@router.get("", response_model=list[CompanyRead])
def list_companies(
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[CompanyRead]:
    statement = select(Company).order_by(Company.verification_status.desc(), Company.company_name.asc())
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Company.company_name.ilike(term),
                Company.industry.ilike(term),
                Company.company_type.ilike(term),
                Company.website.ilike(term),
            )
        )
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    companies = db.scalars(statement).all()
    return [company_response(db, company) for company in companies]


@router.post("/claim", response_model=CompanyClaimRead, status_code=status.HTTP_201_CREATED)
def create_company_claim(
    payload: CompanyClaimCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyClaimRead:
    domain = payload.requested_domain
    ensure_domain_matches(payload.official_email, domain)
    existing_company = find_company_by_normalized_name(db, payload.requested_company_name)
    if existing_company and existing_company.verification_status == CompanyVerificationStatus.VERIFIED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This verified company already exists. Request to join the verified company instead.",
        )
    company = existing_company
    if company is None:
        company = Company(
            company_name=payload.requested_company_name,
            website=f"https://{domain}",
            official_email_domain=domain,
            verification_status=CompanyVerificationStatus.PENDING.value,
        )
        db.add(company)
        db.flush()

    token, token_hash, expires_at = create_claim_token()
    risk_score, risk_level, reasons = assess_company_claim_risk(payload.requested_company_name, domain, str(payload.official_email))
    claim = CompanyClaimRequest(
        company_id=company.id,
        requested_company_name=payload.requested_company_name,
        requested_domain=domain,
        requester_user_id=current_user.id,
        official_email=str(payload.official_email).lower(),
        claim_status=CompanyClaimStatus.PENDING.value,
        verification_token_hash=token_hash,
        token_expires_at=expires_at,
        risk_score=risk_score,
        risk_level=risk_level,
        requires_admin_review=risk_score >= 61,
        risk_reasons=claim_risk_reasons_json(reasons),
    )
    db.add(claim)
    db.flush()
    ensure_company_member(
        db,
        company.id,
        current_user.id,
        CompanyMemberRole.COMPANY_OWNER.value,
        RecruiterVerificationStatus.PENDING.value,
        "Company claim is pending official email verification.",
    )
    notify_admins(
        db,
        "Company claim created",
        f"{current_user.name} requested to claim {payload.requested_company_name}.",
        "COMPANY_CLAIM_CREATED",
        "/admin/dashboard",
    )
    if claim.requires_admin_review:
        notify_admins(
            db,
            "Company claim requires review",
            f"{payload.requested_company_name} matched reserved-name risk checks.",
            "COMPANY_CLAIM_REVIEW",
            "/admin/dashboard",
        )
    db.commit()
    db.refresh(claim)
    log_company_claim_token(claim, token)
    return claim_response(claim)


@router.get("/claim/{token}", response_model=CompanyClaimRead)
def inspect_company_claim_token(token: str, db: Annotated[Session, Depends(get_db)]) -> CompanyClaimRead:
    claim = db.scalar(
        select(CompanyClaimRequest)
        .options(joinedload(CompanyClaimRequest.company), joinedload(CompanyClaimRequest.requester))
        .where(CompanyClaimRequest.verification_token_hash == hash_verification_token(token))
    )
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company claim token not found.")
    if claim.token_expires_at and claim.token_expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        claim.claim_status = CompanyClaimStatus.EXPIRED.value
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company claim token has expired.")
    return claim_response(claim)


@router.post("/claim/{token}/verify", response_model=CompanyClaimVerifyRead)
def verify_company_claim_token(token: str, db: Annotated[Session, Depends(get_db)]) -> CompanyClaimVerifyRead:
    claim = db.scalar(
        select(CompanyClaimRequest)
        .options(joinedload(CompanyClaimRequest.company), joinedload(CompanyClaimRequest.requester))
        .where(CompanyClaimRequest.verification_token_hash == hash_verification_token(token))
    )
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company claim token not found.")
    if claim.claim_status != CompanyClaimStatus.PENDING.value:
        return CompanyClaimVerifyRead(message="Company claim has already been processed.", claim=claim_response(claim))
    if claim.token_expires_at and claim.token_expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        claim.claim_status = CompanyClaimStatus.EXPIRED.value
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company claim token has expired.")
    if email_domain(claim.official_email) != claim.requested_domain:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Official email domain no longer matches claim domain.")
    claim.email_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
    claim.verification_token_hash = None
    claim.token_expires_at = None
    if claim.requires_admin_review:
        claim.admin_note = "Official domain email verified. Owner/Admin review is required before company verification."
        notify_admins(
            db,
            "Company claim email verified",
            f"{claim.requested_company_name} is ready for reserved-name review.",
            "COMPANY_CLAIM_EMAIL_VERIFIED",
            "/admin/dashboard",
        )
        message = "Official email verified. This company claim is waiting for Owner/Admin review."
    else:
        finalize_claim_as_verified(db, claim)
        message = "Company claim verified successfully."
    db.commit()
    db.refresh(claim)
    return CompanyClaimVerifyRead(message=message, claim=claim_response(claim))


@router.post("/{company_id}/join-request", response_model=CompanyJoinRequestRead, status_code=status.HTTP_201_CREATED)
def request_company_join(
    company_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyJoinRequestRead:
    company = db.get(Company, company_id)
    if company is None or company.verification_status != CompanyVerificationStatus.VERIFIED.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verified company not found.")
    member = ensure_company_member(
        db,
        company.id,
        current_user.id,
        CompanyMemberRole.COMPANY_RECRUITER.value,
        RecruiterVerificationStatus.PENDING.value,
        "Recruiter requested to join this verified company.",
    )
    db.flush()
    notify_company_managers(
        db,
        company.id,
        "Recruiter join request",
        f"{current_user.name} requested to join {company.company_name}.",
        "COMPANY_JOIN_REQUEST",
    )
    db.commit()
    db.refresh(member)
    return member_response(member)


@router.get("/{company_id}/members", response_model=list[CompanyJoinRequestRead])
def company_members(
    company_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[CompanyJoinRequestRead]:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    if current_user.role not in {UserRole.OWNER.value, UserRole.ADMIN.value}:
        member = get_company_member(db, company_id, current_user.id)
        if member is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view company members.")
    members = db.scalars(
        select(CompanyMember)
        .options(joinedload(CompanyMember.user), joinedload(CompanyMember.company))
        .where(CompanyMember.company_id == company_id)
        .order_by(CompanyMember.company_role.asc(), CompanyMember.created_at.desc())
    ).all()
    return [member_response(member) for member in members]


@router.put("/members/{member_id}/approve", response_model=CompanyJoinRequestRead)
def approve_member(
    member_id: int,
    payload: CompanyMemberActionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyJoinRequestRead:
    member = db.scalar(
        select(CompanyMember).options(joinedload(CompanyMember.user), joinedload(CompanyMember.company)).where(CompanyMember.id == member_id)
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company member request not found.")
    actor_membership = user_can_manage_company_members(db, current_user, member.company_id)
    if actor_membership and actor_membership.company_role == CompanyMemberRole.COMPANY_ADMIN.value and member.company_role != CompanyMemberRole.COMPANY_RECRUITER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company admins can approve normal recruiters only.")
    approve_company_member(db, member, current_user, payload.note)
    db.commit()
    db.refresh(member)
    return member_response(member)


@router.put("/members/{member_id}/reject", response_model=CompanyJoinRequestRead)
def reject_member(
    member_id: int,
    payload: CompanyMemberActionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyJoinRequestRead:
    member = db.scalar(
        select(CompanyMember).options(joinedload(CompanyMember.user), joinedload(CompanyMember.company)).where(CompanyMember.id == member_id)
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company member request not found.")
    actor_membership = user_can_manage_company_members(db, current_user, member.company_id)
    if actor_membership and member.company_role == CompanyMemberRole.COMPANY_OWNER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company owner cannot be rejected by lower company admins.")
    reject_company_member(db, member, current_user, payload.note)
    db.commit()
    db.refresh(member)
    return member_response(member)


@router.put("/members/{member_id}/role", response_model=CompanyJoinRequestRead)
def update_member_role(
    member_id: int,
    payload: CompanyMemberRoleUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyJoinRequestRead:
    member = db.scalar(
        select(CompanyMember).options(joinedload(CompanyMember.user), joinedload(CompanyMember.company)).where(CompanyMember.id == member_id)
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company member not found.")
    ensure_company_owner_or_platform_admin(db, current_user, member.company_id)
    if member.company_role == CompanyMemberRole.COMPANY_OWNER.value and current_user.role not in {UserRole.OWNER.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company owner cannot be changed by company users.")
    member.company_role = payload.company_role.value
    member.note = payload.note or member.note
    db.commit()
    db.refresh(member)
    return member_response(member)


@router.get("/{company_id}/reviews", response_model=list[CompanyReviewRead])
def company_reviews(company_id: int, db: Annotated[Session, Depends(get_db)]) -> list[CompanyReviewRead]:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    reviews = db.scalars(
        select(CompanyReview)
        .options(joinedload(CompanyReview.job_seeker))
        .where(CompanyReview.company_id == company_id)
        .where(CompanyReview.is_visible.is_(True))
        .order_by(CompanyReview.created_at.desc(), CompanyReview.id.desc())
    ).all()
    return [review_response(review) for review in reviews]


@router.get("/{company_id}/review-summary", response_model=CompanyReviewSummaryRead)
def company_review_summary_endpoint(company_id: int, db: Annotated[Session, Depends(get_db)]) -> CompanyReviewSummaryRead:
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyReviewSummaryRead(**company_review_summary(db, company_id))


@router.get("/{company_id}/analytics", response_model=CompanyReviewSummaryRead)
def company_review_analytics(company_id: int, db: Annotated[Session, Depends(get_db)]) -> CompanyReviewSummaryRead:
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyReviewSummaryRead(**company_review_summary(db, company_id))


@router.post("/{company_id}/reviews", response_model=CompanyReviewRead, status_code=status.HTTP_201_CREATED)
def create_company_review(
    company_id: int,
    payload: CompanyReviewCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyReviewRead:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    application_id = db.scalar(
        select(Application.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.job_seeker_id == current_user.id)
        .where(Job.company_id == company_id)
        .order_by(Application.created_at.desc(), Application.id.desc())
        .limit(1)
    )
    if application_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can review this company after applying to one of its jobs.",
        )
    existing = db.scalar(
        select(CompanyReview)
        .where(CompanyReview.company_id == company_id)
        .where(CompanyReview.job_seeker_id == current_user.id)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already reviewed this company.")
    should_flag = contains_abusive_language(payload.review_title, payload.review_text, payload.pros, payload.cons)
    review = CompanyReview(
        company_id=company_id,
        job_seeker_id=current_user.id,
        application_id=application_id,
        rating=payload.overall_rating,
        overall_rating=payload.overall_rating,
        work_culture_rating=payload.work_culture_rating,
        interview_process_rating=payload.interview_process_rating,
        salary_transparency_rating=payload.salary_transparency_rating,
        growth_opportunity_rating=payload.growth_opportunity_rating,
        review_title=payload.review_title,
        review_text=payload.review_text,
        pros=payload.pros,
        cons=payload.cons,
        is_anonymous=payload.is_anonymous,
        is_visible=not should_flag,
        moderation_status=ReviewModerationStatus.FLAGGED.value if should_flag else ReviewModerationStatus.VISIBLE.value,
    )
    db.add(review)
    db.flush()
    recalculate_company_rating(db, company_id)
    db.commit()
    db.refresh(review)
    review.job_seeker = current_user
    return review_response(review)


@router.get("/{company_id}", response_model=CompanyDetailRead)
def company_detail(
    company_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> CompanyDetailRead:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    summary = company_response(db, company)
    recruiters = db.scalars(
        select(RecruiterProfile)
        .options(joinedload(RecruiterProfile.recruiter))
        .where(RecruiterProfile.company_id == company_id)
        .order_by(RecruiterProfile.created_at.asc())
    ).all()
    active_jobs: list[Job] = []
    if company.verification_status == CompanyVerificationStatus.VERIFIED.value:
        active_jobs = list(db.scalars(public_jobs_statement(company_id).order_by(Job.created_at.desc()).limit(20)).all())
    return CompanyDetailRead(
        **summary.model_dump(),
        recruiters=[
            CompanyRecruiterRead(
                id=profile.id,
                user_id=profile.user_id,
                recruiter_name=profile.recruiter.name if profile.recruiter else "Recruiter",
                recruiter_email=profile.recruiter.email if profile.recruiter else "",
                designation=profile.designation,
                department=profile.department,
                official_email=profile.official_email,
                recruiter_verification_status=profile.recruiter_verification_status,
                account_status=profile.recruiter.account_status if profile.recruiter else "SUSPENDED",
                verified_at=profile.verified_at,
                average_rating=profile.average_rating,
                total_reviews=profile.total_reviews,
            )
            for profile in recruiters
        ],
        active_jobs=[JobRead.model_validate(job) for job in active_jobs],
    )
