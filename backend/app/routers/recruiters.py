from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.application import Application
from app.models.chat_thread import ChatThread
from app.models.company import Company
from app.models.enums import (
    AccountStatus,
    JobModerationStatus,
    RecruiterVerificationStatus,
    ReviewModerationStatus,
    UserRole,
)
from app.models.job import Job
from app.models.recruiter_profile import RecruiterProfile
from app.models.recruiter_review import RecruiterReview
from app.models.user import User
from app.schemas.job import JobRead
from app.schemas.review import RecruiterPublicRead, RecruiterReviewCreate, RecruiterReviewRead, RecruiterReviewSummaryRead
from app.services.recruiter_reviews import recalculate_recruiter_rating, recruiter_review_summary
from app.services.review_moderation import contains_abusive_language
from app.utils.pagination import LimitQuery, PageQuery, pagination_offset

router = APIRouter(prefix="/recruiters", tags=["Recruiters"])


def public_recruiter_jobs_statement(recruiter_id: int):
    return (
        select(Job)
        .join(RecruiterProfile, Job.recruiter_id == RecruiterProfile.user_id)
        .join(Company, Job.company_id == Company.id)
        .join(User, Job.recruiter_id == User.id)
        .where(Job.recruiter_id == recruiter_id)
        .where(Job.company_id == RecruiterProfile.company_id)
        .where(Job.is_active.is_(True))
        .where(Job.deadline >= date.today())
        .where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
        .where(Company.verification_status == "VERIFIED")
        .where(RecruiterProfile.recruiter_verification_status == RecruiterVerificationStatus.VERIFIED.value)
        .where(User.account_status == AccountStatus.ACTIVE.value)
    )


def load_recruiter_profile(db: Session, recruiter_id: int) -> RecruiterProfile:
    profile = db.scalar(
        select(RecruiterProfile)
        .options(joinedload(RecruiterProfile.recruiter), joinedload(RecruiterProfile.company))
        .where(RecruiterProfile.user_id == recruiter_id)
    )
    if profile is None or profile.recruiter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")
    return profile


def recruiter_public_response(db: Session, profile: RecruiterProfile) -> RecruiterPublicRead:
    active_jobs_count = db.scalar(select(func.count()).select_from(public_recruiter_jobs_statement(profile.user_id).subquery())) or 0
    company = profile.company
    return RecruiterPublicRead(
        id=profile.user_id,
        name=profile.recruiter.name,
        company_id=profile.company_id,
        company_name=company.company_name if company else None,
        company_logo_url=company.company_logo_url if company else None,
        company_verification_status=company.verification_status if company else None,
        designation=profile.designation,
        department=profile.department,
        recruiter_verification_status=profile.recruiter_verification_status,
        average_rating=profile.average_rating,
        total_reviews=profile.total_reviews,
        active_jobs_count=active_jobs_count,
        created_at=profile.created_at,
    )


def recruiter_review_response(review: RecruiterReview, admin_view: bool = False) -> RecruiterReviewRead:
    profile = review.recruiter.recruiter_profile if review.recruiter else None
    company = profile.company if profile else None
    return RecruiterReviewRead(
        id=review.id,
        recruiter_id=review.recruiter_id,
        job_seeker_id=review.job_seeker_id,
        application_id=review.application_id,
        overall_rating=review.overall_rating,
        communication_rating=review.communication_rating,
        response_time_rating=review.response_time_rating,
        professionalism_rating=review.professionalism_rating,
        transparency_rating=review.transparency_rating,
        review_title=review.review_title,
        review_text=review.review_text,
        is_anonymous=review.is_anonymous,
        is_visible=review.is_visible,
        moderation_status=review.moderation_status,
        reviewer_name=(review.job_seeker.name if review.job_seeker else None) if admin_view or not review.is_anonymous else None,
        recruiter_name=review.recruiter.name if review.recruiter else None,
        recruiter_email=review.recruiter.email if admin_view and review.recruiter else None,
        company_name=company.company_name if company else None,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def eligible_application_id(db: Session, recruiter_id: int, job_seeker_id: int) -> int | None:
    application_id = db.scalar(
        select(Application.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.job_seeker_id == job_seeker_id)
        .where(Job.recruiter_id == recruiter_id)
        .order_by(Application.created_at.desc(), Application.id.desc())
        .limit(1)
    )
    if application_id is not None:
        return application_id
    return db.scalar(
        select(ChatThread.application_id)
        .where(ChatThread.recruiter_id == recruiter_id)
        .where(ChatThread.job_seeker_id == job_seeker_id)
        .order_by(ChatThread.created_at.desc(), ChatThread.id.desc())
        .limit(1)
    )


@router.get("/{recruiter_id}", response_model=RecruiterPublicRead)
def recruiter_profile(recruiter_id: int, db: Annotated[Session, Depends(get_db)]) -> RecruiterPublicRead:
    return recruiter_public_response(db, load_recruiter_profile(db, recruiter_id))


@router.get("/{recruiter_id}/jobs", response_model=list[JobRead])
def recruiter_public_jobs(
    recruiter_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
) -> list[JobRead]:
    load_recruiter_profile(db, recruiter_id)
    jobs = db.scalars(
        public_recruiter_jobs_statement(recruiter_id)
        .order_by(Job.created_at.desc())
        .offset(pagination_offset(page, limit))
        .limit(limit)
    ).all()
    return [JobRead.model_validate(job) for job in jobs]


@router.get("/{recruiter_id}/reviews", response_model=list[RecruiterReviewRead])
def recruiter_reviews(recruiter_id: int, db: Annotated[Session, Depends(get_db)]) -> list[RecruiterReviewRead]:
    load_recruiter_profile(db, recruiter_id)
    reviews = db.scalars(
        select(RecruiterReview)
        .options(joinedload(RecruiterReview.job_seeker), joinedload(RecruiterReview.recruiter).joinedload(User.recruiter_profile).joinedload(RecruiterProfile.company))
        .where(RecruiterReview.recruiter_id == recruiter_id)
        .where(RecruiterReview.is_visible.is_(True))
        .order_by(RecruiterReview.created_at.desc(), RecruiterReview.id.desc())
    ).all()
    return [recruiter_review_response(review) for review in reviews]


@router.get("/{recruiter_id}/review-summary", response_model=RecruiterReviewSummaryRead)
def recruiter_review_summary_endpoint(recruiter_id: int, db: Annotated[Session, Depends(get_db)]) -> RecruiterReviewSummaryRead:
    load_recruiter_profile(db, recruiter_id)
    return RecruiterReviewSummaryRead(**recruiter_review_summary(db, recruiter_id))


@router.get("/{recruiter_id}/analytics", response_model=RecruiterReviewSummaryRead)
def recruiter_review_analytics(recruiter_id: int, db: Annotated[Session, Depends(get_db)]) -> RecruiterReviewSummaryRead:
    load_recruiter_profile(db, recruiter_id)
    return RecruiterReviewSummaryRead(**recruiter_review_summary(db, recruiter_id))


@router.post("/{recruiter_id}/reviews", response_model=RecruiterReviewRead, status_code=status.HTTP_201_CREATED)
def create_recruiter_review(
    recruiter_id: int,
    payload: RecruiterReviewCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> RecruiterReviewRead:
    profile = load_recruiter_profile(db, recruiter_id)
    if profile.recruiter.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recruiters cannot review themselves.")
    application_id = eligible_application_id(db, recruiter_id, current_user.id)
    if application_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can review this recruiter after applying to one of their jobs.")
    existing = db.scalar(
        select(RecruiterReview)
        .where(RecruiterReview.recruiter_id == recruiter_id)
        .where(RecruiterReview.job_seeker_id == current_user.id)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already reviewed this recruiter.")
    should_flag = contains_abusive_language(payload.review_title, payload.review_text)
    review = RecruiterReview(
        recruiter_id=recruiter_id,
        job_seeker_id=current_user.id,
        application_id=application_id,
        overall_rating=payload.overall_rating,
        communication_rating=payload.communication_rating,
        response_time_rating=payload.response_time_rating,
        professionalism_rating=payload.professionalism_rating,
        transparency_rating=payload.transparency_rating,
        review_title=payload.review_title,
        review_text=payload.review_text,
        is_anonymous=payload.is_anonymous,
        is_visible=not should_flag,
        moderation_status=ReviewModerationStatus.FLAGGED.value if should_flag else ReviewModerationStatus.VISIBLE.value,
    )
    db.add(review)
    db.flush()
    recalculate_recruiter_rating(db, recruiter_id)
    db.commit()
    db.refresh(review)
    review.job_seeker = current_user
    review.recruiter = profile.recruiter
    return recruiter_review_response(review)
