from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
from app.services.rate_limiter import rate_limit_key, rate_limiter
from app.services.user_risk_assessment import update_user_risk

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/job/{job_id}", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def report_job(
    job_id: int,
    payload: ReportCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Report:
    rate_limiter.check(rate_limit_key("reports", request, current_user.id), max_attempts=5, window_seconds=60 * 60)
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
    recruiter = db.get(User, job.recruiter_id)
    if recruiter:
        update_user_risk(db, recruiter)
    db.commit()
    db.refresh(report)
    return report


@router.post("/recruiter/{recruiter_id}", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def report_recruiter(
    recruiter_id: int,
    payload: ReportCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Report:
    rate_limiter.check(rate_limit_key("reports", request, current_user.id), max_attempts=5, window_seconds=60 * 60)
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
    update_user_risk(db, recruiter)
    db.commit()
    db.refresh(report)
    return report
