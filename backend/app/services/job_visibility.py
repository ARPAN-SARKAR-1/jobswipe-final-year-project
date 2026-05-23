from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.models.enums import AccountStatus, CompanyVerificationStatus, JobModerationStatus, RecruiterVerificationStatus
from app.models.job import Job
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User


def get_verified_recruiter_profile_for_job(db: Session, job: Job) -> RecruiterProfile | None:
    if job.company_id is None:
        return None
    return db.scalar(
        select(RecruiterProfile)
        .join(User, RecruiterProfile.user_id == User.id)
        .join(Company, RecruiterProfile.company_id == Company.id)
        .options(joinedload(RecruiterProfile.company), joinedload(RecruiterProfile.recruiter))
        .where(RecruiterProfile.user_id == job.recruiter_id)
        .where(RecruiterProfile.company_id == job.company_id)
        .where(RecruiterProfile.recruiter_verification_status == RecruiterVerificationStatus.VERIFIED.value)
        .where(Company.verification_status == CompanyVerificationStatus.VERIFIED.value)
        .where(User.account_status == AccountStatus.ACTIVE.value)
    )


def is_public_job_available(db: Session, job: Job | None) -> bool:
    if job is None:
        return False
    if not job.is_active or job.deadline < date.today() or job.moderation_status != JobModerationStatus.ACTIVE.value:
        return False
    return get_verified_recruiter_profile_for_job(db, job) is not None


def ensure_public_job_available(db: Session, job: Job | None, detail: str, not_found: bool = False) -> Job:
    if not is_public_job_available(db, job):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if not_found else status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
    return job
