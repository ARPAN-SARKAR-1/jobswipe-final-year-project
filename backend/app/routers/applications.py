from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.application import Application
from app.models.application_timeline import ApplicationTimeline
from app.models.company_profile import CompanyProfile
from app.models.enums import (
    AccountStatus,
    ApplicationAdminStatus,
    ApplicationStatus,
    JobModerationStatus,
    RecruiterVerificationStatus,
    UserRole,
)
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationTimelineRead
from app.services.timeline import add_timeline_event
from app.utils.match_score import calculate_match_score

router = APIRouter(prefix="/applications", tags=["Applications"])


def create_or_reactivate_application(db: Session, user: User, job: Job, payload: ApplicationCreate | None = None) -> Application:
    existing = db.scalar(
        select(Application).where(Application.job_seeker_id == user.id).where(Application.job_id == job.id)
    )
    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == user.id))
    resume_url = payload.resume_pdf_url if payload and payload.resume_pdf_url else (profile.resume_pdf_url if profile else None)
    github_url = payload.github_url if payload and payload.github_url else (profile.github_url if profile else None)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You have already applied to this job. Current status: {existing.status}.",
        )

    application = Application(
        job_seeker_id=user.id,
        job_id=job.id,
        resume_pdf_url=resume_url,
        github_url=github_url,
        status=ApplicationStatus.APPLIED.value,
    )
    db.add(application)
    db.flush()
    add_timeline_event(
        db,
        application.id,
        "APPLIED",
        old_status=None,
        new_status=ApplicationStatus.APPLIED.value,
        note="Application submitted",
        created_by_user_id=user.id,
    )
    db.commit()
    db.refresh(application)
    return application


def apply_match_to_application(application: Application, db: Session, user: User) -> Application:
    if application.job and user.role == UserRole.JOB_SEEKER.value:
        profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == user.id))
        score = calculate_match_score(application.job, profile)
        for key, value in score.items():
            setattr(application.job, key, value)
        setattr(application.job, "existing_application_status", application.status)
    return application


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    payload: ApplicationCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Application:
    if current_user.account_status == AccountStatus.SUSPENDED.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suspended users cannot apply to jobs")
    job = db.get(Job, payload.job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if (
        not job.is_active
        or job.deadline < date.today()
        or job.moderation_status != JobModerationStatus.ACTIVE.value
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This job is not accepting applications")
    company = db.scalar(select(CompanyProfile).where(CompanyProfile.recruiter_id == job.recruiter_id))
    if company is None or company.recruiter_verification_status != RecruiterVerificationStatus.VERIFIED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This recruiter is not verified")
    return create_or_reactivate_application(db, current_user, job, payload)


@router.get("/my", response_model=list[ApplicationRead])
def my_applications(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[Application]:
    applications = list(
        db.scalars(
            select(Application)
            .options(joinedload(Application.job), joinedload(Application.chat_thread))
            .where(Application.job_seeker_id == current_user.id)
            .order_by(Application.created_at.desc())
        ).all()
    )
    return [apply_match_to_application(application, db, current_user) for application in applications]


@router.put("/{application_id}/withdraw", response_model=ApplicationRead)
def withdraw_application(
    application_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Application:
    application = db.scalar(
        select(Application)
        .options(joinedload(Application.job), joinedload(Application.chat_thread))
        .where(Application.id == application_id)
        .where(Application.job_seeker_id == current_user.id)
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application.status != ApplicationStatus.APPLIED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only applied applications can be withdrawn")

    application.status = ApplicationStatus.WITHDRAWN.value
    add_timeline_event(
        db,
        application.id,
        "WITHDRAWN",
        old_status=ApplicationStatus.APPLIED.value,
        new_status=ApplicationStatus.WITHDRAWN.value,
        note="Application withdrawn by job seeker",
        created_by_user_id=current_user.id,
    )
    db.commit()
    db.refresh(application)
    return application


@router.get("/{application_id}/timeline", response_model=list[ApplicationTimelineRead])
def application_timeline(
    application_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ApplicationTimeline]:
    application = db.scalar(
        select(Application)
        .options(joinedload(Application.job))
        .where(Application.id == application_id)
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    allowed = application.job_seeker_id == current_user.id
    if application.job and application.job.recruiter_id == current_user.id:
        allowed = True
    if current_user.role in {UserRole.ADMIN.value, UserRole.OWNER.value}:
        allowed = True
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return list(
        db.scalars(
            select(ApplicationTimeline)
            .where(ApplicationTimeline.application_id == application.id)
            .order_by(ApplicationTimeline.created_at.asc(), ApplicationTimeline.id.asc())
        ).all()
    )
