from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.application import Application
from app.models.company_profile import CompanyProfile
from app.models.enums import AccountStatus, ApplicationStatus, JobModerationStatus, RecruiterVerificationStatus, SwipeAction, UserRole
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.swipe import Swipe
from app.models.user import User
from app.routers.applications import create_or_reactivate_application
from app.schemas.swipe import SwipeCreate, SwipeRead, UndoSwipeResponse
from app.utils.match_score import calculate_match_score

router = APIRouter(prefix="/swipes", tags=["Swipes"])


@router.post("", response_model=SwipeRead, status_code=status.HTTP_201_CREATED)
def create_swipe(
    payload: SwipeCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Swipe:
    if current_user.account_status == AccountStatus.SUSPENDED.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suspended users cannot swipe or apply")
    job = db.get(Job, payload.job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if not job.is_active or job.deadline < date.today() or job.moderation_status != JobModerationStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This job is no longer active")
    company = db.scalar(select(CompanyProfile).where(CompanyProfile.recruiter_id == job.recruiter_id))
    if company is None or company.recruiter_verification_status != RecruiterVerificationStatus.VERIFIED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This recruiter is not verified")

    swipe = Swipe(job_seeker_id=current_user.id, job_id=job.id, action=payload.action.value)
    db.add(swipe)
    db.flush()
    if payload.action == SwipeAction.LIKE:
        create_or_reactivate_application(db, current_user, job)
    else:
        db.commit()
    db.refresh(swipe)
    return swipe


@router.get("/history", response_model=list[SwipeRead])
def swipe_history(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[Swipe]:
    swipes = list(
        db.scalars(
            select(Swipe)
            .options(joinedload(Swipe.job))
            .where(Swipe.job_seeker_id == current_user.id)
            .order_by(Swipe.created_at.desc(), Swipe.id.desc())
        ).all()
    )
    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == current_user.id))
    applications = db.scalars(select(Application).where(Application.job_seeker_id == current_user.id)).all()
    application_statuses = {application.job_id: application.status for application in applications}
    for swipe in swipes:
        if swipe.job:
            score = calculate_match_score(swipe.job, profile)
            for key, value in score.items():
                setattr(swipe.job, key, value)
            setattr(swipe.job, "existing_application_status", application_statuses.get(swipe.job.id))
    return swipes


@router.post("/undo", response_model=UndoSwipeResponse)
def undo_last_swipe(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> UndoSwipeResponse:
    swipe = db.scalar(
        select(Swipe)
        .options(joinedload(Swipe.job))
        .where(Swipe.job_seeker_id == current_user.id)
        .order_by(Swipe.created_at.desc(), Swipe.id.desc())
        .limit(1)
    )
    if swipe is None:
        return UndoSwipeResponse(message="No swipe to undo", undone=None)

    undone = SwipeRead.model_validate(swipe)
    if swipe.action == SwipeAction.LIKE.value:
        application = db.scalar(
            select(Application)
            .where(Application.job_seeker_id == current_user.id)
            .where(Application.job_id == swipe.job_id)
            .where(Application.status == ApplicationStatus.APPLIED.value)
        )
        if application:
            db.delete(application)

    db.delete(swipe)
    db.commit()
    return UndoSwipeResponse(message="Last swipe undone", undone=undone)


@router.delete("/saved/{job_id}")
def unsave_job(
    job_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    db.execute(
        delete(Swipe)
        .where(Swipe.job_seeker_id == current_user.id)
        .where(Swipe.job_id == job_id)
        .where(Swipe.action == SwipeAction.SAVE.value)
    )
    db.commit()
    return {"message": "Job removed from saved list"}
