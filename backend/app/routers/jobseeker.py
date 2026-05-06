from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.application import Application
from app.models.enums import JobModerationStatus, UserRole
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.swipe import Swipe
from app.models.user import User
from app.schemas.profile import JobSeekerProfileRead, JobSeekerProfileUpdate, UploadResponse
from app.utils.file_upload import save_image, save_resume_pdf

router = APIRouter(prefix="/jobseeker", tags=["Job Seeker"])


def get_or_create_profile(db: Session, user_id: int) -> JobSeekerProfile:
    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == user_id))
    if profile is None:
        profile = JobSeekerProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def profile_response(profile: JobSeekerProfile, user: User) -> JobSeekerProfileRead:
    return JobSeekerProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        name=user.name,
        email=user.email,
        profile_picture_url=user.profile_picture_url,
        resume_pdf_url=profile.resume_pdf_url,
        phone=profile.phone,
        github_url=profile.github_url,
        education=profile.education,
        degree=profile.degree,
        college=profile.college,
        passing_year=profile.passing_year,
        cgpa_or_percentage=profile.cgpa_or_percentage,
        skills=profile.skills,
        experience_level=profile.experience_level,
        preferred_location=profile.preferred_location,
        preferred_job_type=profile.preferred_job_type,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/dashboard")
def dashboard(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    profile = get_or_create_profile(db, current_user.id)
    fields = [
        current_user.profile_picture_url,
        profile.phone,
        profile.github_url,
        profile.resume_pdf_url,
        profile.education,
        profile.degree,
        profile.college,
        profile.skills,
        profile.experience_level,
        profile.preferred_location,
        profile.preferred_job_type,
    ]
    completion = round(sum(1 for value in fields if value) / len(fields) * 100)

    viewed_jobs = select(Swipe.job_id).where(Swipe.job_seeker_id == current_user.id)
    recommended_count = db.scalar(
        select(func.count(Job.id))
        .where(Job.is_active.is_(True))
        .where(Job.deadline >= date.today())
        .where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
        .where(Job.id.not_in(viewed_jobs))
    )
    saved_count = db.scalar(
        select(func.count(func.distinct(Swipe.job_id)))
        .where(Swipe.job_seeker_id == current_user.id)
        .where(Swipe.action == "SAVE")
    )
    applications_count = db.scalar(
        select(func.count(Application.id)).where(Application.job_seeker_id == current_user.id)
    )
    return {
        "name": current_user.name,
        "profile_completion": completion,
        "recommended_jobs_count": recommended_count or 0,
        "saved_jobs_count": saved_count or 0,
        "applications_count": applications_count or 0,
    }


@router.get("/profile", response_model=JobSeekerProfileRead)
def get_profile(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerProfileRead:
    profile = get_or_create_profile(db, current_user.id)
    return profile_response(profile, current_user)


@router.put("/profile", response_model=JobSeekerProfileRead)
def update_profile(
    payload: JobSeekerProfileUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerProfileRead:
    profile = get_or_create_profile(db, current_user.id)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile_response(profile, current_user)


@router.post("/profile-picture", response_model=UploadResponse)
async def upload_profile_picture(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> UploadResponse:
    url = await save_image(file, "profile-pictures")
    current_user.profile_picture_url = url
    db.commit()
    return UploadResponse(url=url, message="Profile picture uploaded")


@router.post("/resume", response_model=UploadResponse)
async def upload_resume(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> UploadResponse:
    profile = get_or_create_profile(db, current_user.id)
    url = await save_resume_pdf(file)
    profile.resume_pdf_url = url
    db.commit()
    return UploadResponse(url=url, message="Resume uploaded")
