from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.enums import JobModerationStatus, ReportStatus, UserRole
from app.models.job import Job
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead
from app.services.notifications import notify_admins

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/job/{job_id}", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def report_job(
    job_id: int,
    payload: ReportCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Report:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    report = Report(
        reporter_id=current_user.id,
        job_id=job.id,
        recruiter_id=job.recruiter_id,
        report_type=payload.report_type.value,
        description=payload.description.strip(),
        status=ReportStatus.PENDING.value,
    )
    db.add(report)
    db.flush()
    notify_admins(
        db,
        "Job reported",
        f"{current_user.name} reported {job.title}.",
        "JOB_REPORTED",
        "/admin/dashboard",
    )
    db.commit()
    db.refresh(report)
    return report


@router.post("/recruiter/{recruiter_id}", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def report_recruiter(
    recruiter_id: int,
    payload: ReportCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Report:
    recruiter = db.get(User, recruiter_id)
    if recruiter is None or recruiter.role != UserRole.RECRUITER.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")
    report = Report(
        reporter_id=current_user.id,
        recruiter_id=recruiter.id,
        report_type=payload.report_type.value,
        description=payload.description.strip(),
        status=ReportStatus.PENDING.value,
    )
    db.add(report)
    db.flush()
    notify_admins(
        db,
        "Recruiter reported",
        f"A job seeker reported recruiter {recruiter.name}.",
        "JOB_REPORTED",
        "/admin/dashboard",
    )
    db.commit()
    db.refresh(report)
    return report
