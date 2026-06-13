from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company_profile import CompanyProfile
from app.models.enums import CompanyJoinStatus, CompanyVerificationStatus, JobModerationStatus, RecruiterVerificationStatus
from app.models.job import Job
from app.models.recruiter_company_member import RecruiterCompanyMember
from app.models.user import User

SUSPICIOUS_JOB_PHRASES = [
    "joining fee",
    "pay to join",
    "training fee required",
    "security deposit",
    "urgent payment",
    "guaranteed job after payment",
]


def get_recruiter_membership(db: Session, recruiter_id: int, company_id: int | None = None) -> RecruiterCompanyMember | None:
    statement = select(RecruiterCompanyMember).where(RecruiterCompanyMember.recruiter_id == recruiter_id)
    if company_id is not None:
        statement = statement.where(RecruiterCompanyMember.company_id == company_id)
    return db.scalar(statement.order_by(RecruiterCompanyMember.created_at.desc()).limit(1))


def get_or_create_recruiter_membership(db: Session, recruiter: User, company: CompanyProfile) -> RecruiterCompanyMember:
    membership = get_recruiter_membership(db, recruiter.id, company.id)
    if membership is None:
        membership = RecruiterCompanyMember(
            recruiter_id=recruiter.id,
            company_id=company.id,
            verification_status=company.recruiter_verification_status,
            company_join_status=(
                CompanyJoinStatus.APPROVED.value
                if company.recruiter_verification_status == RecruiterVerificationStatus.VERIFIED.value
                else CompanyJoinStatus.PENDING.value
            ),
            verified_at=company.verified_at,
            verified_by_admin_id=company.verified_by_admin_id,
            admin_note=company.verification_note,
        )
        db.add(membership)
        db.flush()
    return membership


def recruiter_can_post_public_job(recruiter: User, company: CompanyProfile | None, membership: RecruiterCompanyMember | None) -> bool:
    return bool(
        recruiter.account_status == "ACTIVE"
        and company is not None
        and company.verification_status == CompanyVerificationStatus.VERIFIED.value
        and membership is not None
        and membership.company_join_status == CompanyJoinStatus.APPROVED.value
        and membership.verification_status == RecruiterVerificationStatus.VERIFIED.value
    )


def assess_job_risk(*parts: str | None) -> tuple[int, list[str]]:
    text = " ".join(part or "" for part in parts).lower()
    flags = [phrase for phrase in SUSPICIOUS_JOB_PHRASES if phrase in text]
    return len(flags), flags


def apply_job_risk(job: Job) -> None:
    score, flags = assess_job_risk(job.title, job.description, job.eligibility, job.bond_details)
    job.risk_score = score
    job.risk_flags = ", ".join(flags) if flags else None
    if score > 0:
        job.moderation_status = JobModerationStatus.PAUSED.value
        job.moderation_reason = "Marked for admin review: suspicious payment language."


def attach_job_trust(db: Session, job: Job) -> Job:
    company = job.company
    if company is None and job.company_id is not None:
        company = db.get(CompanyProfile, job.company_id)
    if company is None:
        company = db.scalar(select(CompanyProfile).where(CompanyProfile.recruiter_id == job.recruiter_id))
    membership = get_recruiter_membership(db, job.recruiter_id, company.id if company else None)
    company_verified = company is not None and company.verification_status == CompanyVerificationStatus.VERIFIED.value
    recruiter_verified = membership is not None and membership.verification_status == RecruiterVerificationStatus.VERIFIED.value
    setattr(job, "company_verified", company_verified)
    setattr(job, "recruiter_verified", recruiter_verified)
    setattr(job, "trusted_posting", company_verified and recruiter_verified)
    setattr(job, "company_verification_status", company.verification_status if company else None)
    setattr(job, "recruiter_verification_status", membership.verification_status if membership else None)
    if company is not None:
        job.company_id = company.id
    return job
