from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.application import Application
from app.models.enums import UserRole
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.user import User

router = APIRouter(prefix="/files", tags=["Files"])


def ensure_safe_resume_filename(filename: str) -> str:
    path = Path(filename)
    if path.name != filename or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return filename


def resume_url_candidates(filename: str) -> list[str]:
    return [f"/api/files/resumes/{filename}", f"/uploads/resumes/{filename}"]


def find_resume_owner_id(db: Session, urls: list[str]) -> int | None:
    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.resume_pdf_url.in_(urls)).limit(1))
    if profile is not None:
        return profile.user_id
    application = db.scalar(select(Application).where(Application.resume_pdf_url.in_(urls)).limit(1))
    return application.job_seeker_id if application else None


def recruiter_can_access_resume(db: Session, recruiter_id: int, job_seeker_id: int) -> bool:
    application_id = db.scalar(
        select(Application.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.job_seeker_id == job_seeker_id)
        .where(Job.recruiter_id == recruiter_id)
        .limit(1)
    )
    return application_id is not None


def job_seeker_can_access_resume(db: Session, job_seeker_id: int, urls: list[str]) -> bool:
    profile_id = db.scalar(
        select(JobSeekerProfile.id)
        .where(JobSeekerProfile.user_id == job_seeker_id)
        .where(JobSeekerProfile.resume_pdf_url.in_(urls))
        .limit(1)
    )
    if profile_id is not None:
        return True
    application_id = db.scalar(
        select(Application.id)
        .where(Application.job_seeker_id == job_seeker_id)
        .where(Application.resume_pdf_url.in_(urls))
        .limit(1)
    )
    return application_id is not None


@router.get("/resumes/{filename}")
def get_resume_file(
    filename: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    safe_filename = ensure_safe_resume_filename(filename)
    resume_path = (settings.upload_path / "resumes" / safe_filename).resolve()
    resume_root = (settings.upload_path / "resumes").resolve()
    try:
        resume_path.relative_to(resume_root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from exc
    if not resume_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    urls = resume_url_candidates(safe_filename)
    owner_id = find_resume_owner_id(db, urls)
    if owner_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if current_user.role in {UserRole.ADMIN.value, UserRole.OWNER.value}:
        return FileResponse(resume_path, media_type="application/pdf", filename=safe_filename)
    if current_user.role == UserRole.JOB_SEEKER.value and job_seeker_can_access_resume(db, current_user.id, urls):
        return FileResponse(resume_path, media_type="application/pdf", filename=safe_filename)
    if current_user.role == UserRole.RECRUITER.value and recruiter_can_access_resume(db, current_user.id, owner_id):
        return FileResponse(resume_path, media_type="application/pdf", filename=safe_filename)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
