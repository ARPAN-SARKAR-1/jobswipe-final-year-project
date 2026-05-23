from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_optional_current_user, require_roles
from app.models.application import Application
from app.models.company import Company
from app.models.company_review import CompanyReview
from app.models.enums import AccountStatus, CompanyVerificationStatus, JobModerationStatus, RecruiterVerificationStatus, UserRole
from app.models.job import Job
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User
from app.schemas.company import (
    CompanyDetailRead,
    CompanyRead,
    CompanyRecruiterRead,
    CompanyReviewCreate,
    CompanyReviewRead,
)
from app.schemas.job import JobRead
from app.services.company_reviews import recalculate_company_rating

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
        rating=review.rating,
        review_text=review.review_text,
        is_visible=review.is_visible,
        reviewer_name=review.job_seeker.name if review.job_seeker else None,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.get("", response_model=list[CompanyRead])
def list_companies(db: Annotated[Session, Depends(get_db)]) -> list[CompanyRead]:
    companies = db.scalars(select(Company).order_by(Company.verification_status.desc(), Company.company_name.asc())).all()
    return [company_response(db, company) for company in companies]


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
    has_applied = db.scalar(
        select(Application.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.job_seeker_id == current_user.id)
        .where(Job.company_id == company_id)
        .limit(1)
    )
    if has_applied is None:
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
    review = CompanyReview(
        company_id=company_id,
        job_seeker_id=current_user.id,
        rating=payload.rating,
        review_text=payload.review_text,
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
            )
            for profile in recruiters
        ],
        active_jobs=[JobRead.model_validate(job) for job in active_jobs],
    )
