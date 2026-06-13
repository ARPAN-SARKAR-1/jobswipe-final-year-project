from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_optional_current_user, require_roles
from app.models.application import Application
from app.models.company_profile import CompanyProfile
from app.models.company_review import CompanyReview
from app.models.enums import ApplicationStatus, CompanyJoinStatus, CompanyVerificationStatus, JobModerationStatus, RecruiterVerificationStatus, ReviewModerationStatus, UserRole
from app.models.job import Job
from app.models.recruiter_company_member import RecruiterCompanyMember
from app.models.user import User
from app.schemas.company import CompanyPublicRead, CompanyReviewCreate, CompanyReviewRead, RecruiterCompanyMemberRead
from app.schemas.job import JobRead
from app.services.trust import attach_job_trust

router = APIRouter(prefix="/companies", tags=["Companies"])

REVIEW_ELIGIBLE_STATUSES = {ApplicationStatus.SHORTLISTED.value, ApplicationStatus.INTERVIEWED.value, ApplicationStatus.HIRED.value}


def review_response(review: CompanyReview) -> CompanyReviewRead:
    return CompanyReviewRead(
        id=review.id,
        company_id=review.company_id,
        reviewer_user_id=review.reviewer_user_id,
        reviewer_name=review.reviewer.name if review.reviewer else None,
        application_id=review.application_id,
        rating=review.rating,
        title=review.title,
        review_text=review.review_text,
        work_culture_rating=review.work_culture_rating,
        interview_process_rating=review.interview_process_rating,
        growth_rating=review.growth_rating,
        is_visible=review.is_visible,
        is_flagged=review.is_flagged,
        moderation_status=review.moderation_status,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def member_response(member: RecruiterCompanyMember) -> RecruiterCompanyMemberRead:
    return RecruiterCompanyMemberRead(
        id=member.id,
        recruiter_id=member.recruiter_id,
        company_id=member.company_id,
        recruiter_name=member.recruiter.name if member.recruiter else None,
        recruiter_email=member.recruiter.email if member.recruiter else None,
        company_name=member.company.company_name if member.company else None,
        designation=member.designation,
        work_email=member.work_email,
        verification_status=member.verification_status,
        company_join_status=member.company_join_status,
        verified_at=member.verified_at,
        verified_by_admin_id=member.verified_by_admin_id,
        verified_by_company_owner_id=member.verified_by_company_owner_id,
        admin_note=member.admin_note,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def company_public_response(db: Session, company: CompanyProfile, include_hidden_reviews: bool = False) -> CompanyPublicRead:
    review_statement = (
        select(CompanyReview)
        .options(joinedload(CompanyReview.reviewer))
        .where(CompanyReview.company_id == company.id)
        .order_by(CompanyReview.created_at.desc())
    )
    if not include_hidden_reviews:
        review_statement = review_statement.where(CompanyReview.is_visible.is_(True)).where(
            CompanyReview.moderation_status == ReviewModerationStatus.VISIBLE.value
        )
    reviews = list(db.scalars(review_statement).all())
    visible_reviews = [review for review in reviews if review.is_visible and review.moderation_status == ReviewModerationStatus.VISIBLE.value]
    average_rating = None
    if visible_reviews:
        average_rating = round(sum(review.rating for review in visible_reviews) / len(visible_reviews), 1)

    verified_members = list(
        db.scalars(
            select(RecruiterCompanyMember)
            .options(joinedload(RecruiterCompanyMember.recruiter), joinedload(RecruiterCompanyMember.company))
            .where(RecruiterCompanyMember.company_id == company.id)
            .where(RecruiterCompanyMember.verification_status == RecruiterVerificationStatus.VERIFIED.value)
            .where(RecruiterCompanyMember.company_join_status == CompanyJoinStatus.APPROVED.value)
        ).all()
    )
    jobs = list(
        db.scalars(
            select(Job)
            .where(Job.company_id == company.id)
            .where(Job.is_active.is_(True))
            .where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
            .order_by(Job.created_at.desc())
            .limit(20)
        ).all()
    )
    jobs = [attach_job_trust(db, job) for job in jobs]

    return CompanyPublicRead(
        id=company.id,
        name=company.company_name,
        company_name=company.company_name,
        logo_url=company.company_logo_url,
        company_logo_url=company.company_logo_url,
        company_type=company.company_type,
        industry=company.industry,
        location=company.location,
        website=company.website,
        description=company.description,
        verification_status=company.verification_status,
        average_rating=average_rating,
        review_count=len(visible_reviews),
        visible_reviews=[review_response(review) for review in reviews],
        verified_recruiter_count=len(verified_members),
        verified_recruiters=[member_response(member) for member in verified_members],
        active_jobs=[JobRead.model_validate(job) for job in jobs],
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


@router.get("/{company_id}", response_model=CompanyPublicRead)
def get_company(
    company_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> CompanyPublicRead:
    company = db.get(CompanyProfile, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    include_hidden = current_user is not None and current_user.role in {UserRole.ADMIN.value, UserRole.OWNER.value}
    return company_public_response(db, company, include_hidden_reviews=include_hidden)


@router.get("", response_model=list[CompanyPublicRead])
def list_companies(db: Annotated[Session, Depends(get_db)]) -> list[CompanyPublicRead]:
    companies = db.scalars(
        select(CompanyProfile)
        .where(CompanyProfile.verification_status == CompanyVerificationStatus.VERIFIED.value)
        .order_by(CompanyProfile.updated_at.desc())
        .limit(50)
    ).all()
    return [company_public_response(db, company) for company in companies]


@router.post("/{company_id}/reviews", response_model=CompanyReviewRead, status_code=status.HTTP_201_CREATED)
def create_company_review(
    company_id: int,
    payload: CompanyReviewCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyReviewRead:
    company = db.get(CompanyProfile, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    existing = db.scalar(
        select(CompanyReview)
        .where(CompanyReview.company_id == company_id)
        .where(CompanyReview.reviewer_user_id == current_user.id)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already reviewed this company.")

    application = db.scalar(
        select(Application)
        .join(Job, Application.job_id == Job.id)
        .where(Application.job_seeker_id == current_user.id)
        .where(Job.company_id == company_id)
        .where(Application.status.in_(REVIEW_ELIGIBLE_STATUSES))
        .order_by(Application.updated_at.desc())
        .limit(1)
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can review this company only after a meaningful application interaction.")

    review = CompanyReview(
        company_id=company.id,
        reviewer_user_id=current_user.id,
        application_id=application.id,
        rating=payload.rating,
        title=payload.title.strip(),
        review_text=payload.review_text.strip(),
        work_culture_rating=payload.work_culture_rating,
        interview_process_rating=payload.interview_process_rating,
        growth_rating=payload.growth_rating,
        is_visible=True,
        is_flagged=False,
        moderation_status=ReviewModerationStatus.VISIBLE.value,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review_response(review)
