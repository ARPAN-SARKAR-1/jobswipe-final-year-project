import json
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.candidate_risk_assessment import CandidateRiskAssessment
from app.models.company_claim_request import CompanyClaimRequest
from app.models.enums import CompanyVerificationStatus, RecruiterVerificationStatus, RiskLevel, UserRole
from app.models.job import Job
from app.models.job_risk_assessment import JobRiskAssessment
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.login_attempt import LoginAttempt
from app.models.recruiter_profile import RecruiterProfile
from app.models.report import Report
from app.models.user import User
from app.models.user_risk_assessment import UserRiskAssessment
from app.services.company_claims import reserved_brand_match


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def risk_level(score: int) -> str:
    if score >= 81:
        return RiskLevel.CRITICAL.value
    if score >= 61:
        return RiskLevel.HIGH.value
    if score >= 31:
        return RiskLevel.MEDIUM.value
    return RiskLevel.LOW.value


def add_reason(reasons: list[str], reason: str) -> None:
    if reason not in reasons:
        reasons.append(reason)


def recent_failed_login_count(db: Session, user: User) -> int:
    cutoff = utc_now_naive() - timedelta(hours=24)
    return db.scalar(
        select(func.count(LoginAttempt.id))
        .where(LoginAttempt.email == user.email.lower())
        .where(LoginAttempt.success.is_(False))
        .where(LoginAttempt.created_at >= cutoff)
    ) or 0


def calculate_job_seeker_risk(db: Session, user: User) -> tuple[int, list[str]]:
    score = 5
    reasons: list[str] = []
    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == user.id))
    if profile is None:
        score += 35
        add_reason(reasons, "Job seeker profile is missing.")
    else:
        missing = [
            label
            for label, value in {
                "resume": profile.resume_pdf_url,
                "skills": profile.skills,
                "education": profile.education,
                "phone": profile.phone,
            }.items()
            if not value
        ]
        if missing:
            score += 8 * len(missing)
            add_reason(reasons, f"Profile is incomplete: {', '.join(missing)} missing.")
        if profile.github_url and "github.com" not in profile.github_url.lower():
            score += 15
            add_reason(reasons, "GitHub URL does not point to github.com.")
        if profile.phone and not re.fullmatch(r"[+\d][\d\s-]{7,20}", profile.phone.strip()):
            score += 10
            add_reason(reasons, "Phone number format looks invalid.")
        if profile.resume_pdf_url:
            duplicate_resume_count = db.scalar(
                select(func.count(JobSeekerProfile.id))
                .where(JobSeekerProfile.resume_pdf_url == profile.resume_pdf_url)
                .where(JobSeekerProfile.user_id != user.id)
            ) or 0
            if duplicate_resume_count:
                score += 20
                add_reason(reasons, "Resume file reference is reused by another account.")

    recent_cutoff = utc_now_naive() - timedelta(hours=24)
    recent_applications = db.scalar(
        select(func.count(Application.id)).where(Application.job_seeker_id == user.id).where(Application.created_at >= recent_cutoff)
    ) or 0
    if recent_applications >= 15:
        score += 30
        add_reason(reasons, "Too many applications were submitted in a short time.")

    candidate_risk = db.scalar(select(CandidateRiskAssessment).where(CandidateRiskAssessment.job_seeker_id == user.id))
    if candidate_risk and candidate_risk.risk_score >= 31:
        score += min(35, candidate_risk.risk_score // 2)
        add_reason(reasons, "Candidate was reported or flagged by recruiter review.")

    if any(part in user.email.lower() for part in ["fake", "spam", "temp", "test"]):
        score += 12
        add_reason(reasons, "Email pattern looks suspicious.")

    failed_logins = recent_failed_login_count(db, user)
    if failed_logins >= 3:
        score += min(25, failed_logins * 5)
        add_reason(reasons, "Multiple failed login attempts were recorded.")

    return min(score, 100), reasons


def calculate_recruiter_risk(db: Session, user: User) -> tuple[int, list[str]]:
    score = 5
    reasons: list[str] = []
    profile = db.scalar(select(RecruiterProfile).where(RecruiterProfile.user_id == user.id))
    company = profile.company if profile and profile.company else None
    if profile is None:
        score += 35
        add_reason(reasons, "Recruiter profile is missing.")
    else:
        if profile.recruiter_verification_status != RecruiterVerificationStatus.VERIFIED.value:
            score += 25
            add_reason(reasons, "Recruiter profile is not verified.")
        if company is None or company.verification_status != CompanyVerificationStatus.VERIFIED.value:
            score += 25
            add_reason(reasons, "Company is not verified.")
        if company:
            match_name, _score = reserved_brand_match(company.company_name)
            if match_name and company.verification_status != CompanyVerificationStatus.VERIFIED.value:
                score += 25
                add_reason(reasons, f"Company name resembles reserved brand {match_name} but is not verified.")
            if company.official_email_domain and profile.official_email and "@" in profile.official_email:
                recruiter_domain = profile.official_email.rsplit("@", 1)[-1].lower()
                if recruiter_domain != company.official_email_domain:
                    score += 15
                    add_reason(reasons, "Recruiter official email domain does not match company domain.")

    recent_cutoff = utc_now_naive() - timedelta(days=7)
    recent_jobs = db.scalar(select(func.count(Job.id)).where(Job.recruiter_id == user.id).where(Job.created_at >= recent_cutoff)) or 0
    if recent_jobs >= 5:
        score += 20
        add_reason(reasons, "Recruiter posted many jobs in a short time.")

    risky_jobs = db.scalar(
        select(func.count(JobRiskAssessment.id))
        .join(Job, JobRiskAssessment.job_id == Job.id)
        .where(Job.recruiter_id == user.id)
        .where(JobRiskAssessment.risk_score >= 31)
    ) or 0
    if risky_jobs:
        score += min(30, risky_jobs * 12)
        add_reason(reasons, "Recruiter has jobs flagged by fake-job risk scoring.")

    reports = db.scalar(select(func.count(Report.id)).where(Report.recruiter_id == user.id)) or 0
    if reports:
        score += min(25, reports * 8)
        add_reason(reasons, "Recruiter has user reports.")

    rejected_claims = db.scalar(
        select(func.count(CompanyClaimRequest.id))
        .where(CompanyClaimRequest.requester_user_id == user.id)
        .where(CompanyClaimRequest.claim_status == "REJECTED")
    ) or 0
    if rejected_claims:
        score += min(25, rejected_claims * 15)
        add_reason(reasons, "Recruiter has rejected company claims.")

    failed_logins = recent_failed_login_count(db, user)
    if failed_logins >= 3:
        score += min(25, failed_logins * 5)
        add_reason(reasons, "Multiple failed login attempts were recorded.")

    return min(score, 100), reasons


def calculate_user_risk(db: Session, user: User) -> tuple[int, list[str]]:
    if user.role == UserRole.RECRUITER.value:
        return calculate_recruiter_risk(db, user)
    if user.role == UserRole.JOB_SEEKER.value:
        return calculate_job_seeker_risk(db, user)
    failed_logins = recent_failed_login_count(db, user)
    score = min(100, failed_logins * 5)
    reasons = ["Multiple failed login attempts were recorded."] if failed_logins >= 3 else []
    return score, reasons


def update_user_risk(db: Session, user_or_id: User | int) -> UserRiskAssessment | None:
    user = user_or_id if isinstance(user_or_id, User) else db.get(User, user_or_id)
    if user is None:
        return None
    score, reasons = calculate_user_risk(db, user)
    assessment = db.scalar(select(UserRiskAssessment).where(UserRiskAssessment.user_id == user.id))
    if assessment is None:
        assessment = UserRiskAssessment(user_id=user.id)
        db.add(assessment)
    assessment.risk_score = score
    assessment.risk_level = risk_level(score)
    assessment.reasons = json.dumps(reasons)
    assessment.last_evaluated_at = utc_now_naive()
    return assessment
