from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.application import Application
from app.models.company_profile import CompanyProfile
from app.models.enums import ApplicationAdminStatus, ApplicationStatus, JobModerationStatus, UserRole
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.user import User
from app.schemas.application import ApplicationStatusUpdate, RecruiterApplicationRead
from app.schemas.job import JobRead
from app.schemas.profile import CompanyProfileRead, CompanyProfileUpdate, UploadResponse
from app.services.notifications import create_notification
from app.services.timeline import add_timeline_event
from app.utils.file_upload import save_image

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


def get_or_create_company(db: Session, recruiter_id: int) -> CompanyProfile:
    company = db.scalar(select(CompanyProfile).where(CompanyProfile.recruiter_id == recruiter_id))
    if company is None:
        company = CompanyProfile(recruiter_id=recruiter_id)
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


@router.get("/dashboard")
def dashboard(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    job_ids = select(Job.id).where(Job.recruiter_id == current_user.id)
    total_jobs = db.scalar(select(func.count(Job.id)).where(Job.recruiter_id == current_user.id)) or 0
    active_jobs = db.scalar(
        select(func.count(Job.id))
        .where(Job.recruiter_id == current_user.id)
        .where(Job.is_active.is_(True))
        .where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
        .where(Job.deadline >= date.today())
    ) or 0
    expired_jobs = db.scalar(
        select(func.count(Job.id))
        .where(Job.recruiter_id == current_user.id)
        .where(Job.deadline < date.today())
    ) or 0
    applications = db.scalar(select(func.count(Application.id)).where(Application.job_id.in_(job_ids))) or 0
    jobs = db.scalars(
        select(Job).where(Job.recruiter_id == current_user.id).order_by(Job.created_at.desc()).limit(8)
    ).all()
    company = get_or_create_company(db, current_user.id)
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "expired_jobs": expired_jobs,
        "applications_received": applications,
        "posted_jobs": [JobRead.model_validate(job).model_dump(mode="json") for job in jobs],
        "company_profile": CompanyProfileRead.model_validate(company).model_dump(mode="json"),
    }


@router.get("/company-profile", response_model=CompanyProfileRead)
def get_company_profile(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyProfile:
    return get_or_create_company(db, current_user.id)


@router.put("/company-profile", response_model=CompanyProfileRead)
def update_company_profile(
    payload: CompanyProfileUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyProfile:
    company = get_or_create_company(db, current_user.id)
    for key, value in payload.model_dump().items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


@router.post("/company-logo", response_model=UploadResponse)
async def upload_company_logo(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> UploadResponse:
    company = get_or_create_company(db, current_user.id)
    url = await save_image(file, "company-logos")
    company.company_logo_url = url
    db.commit()
    return UploadResponse(url=url, message="Company logo uploaded")


@router.get("/applications", response_model=list[RecruiterApplicationRead])
def applications(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[RecruiterApplicationRead]:
    rows = db.scalars(
        select(Application)
        .join(Job)
        .options(
            joinedload(Application.job),
            joinedload(Application.chat_thread),
            joinedload(Application.job_seeker).joinedload(User.job_seeker_profile),
        )
        .where(Job.recruiter_id == current_user.id)
        .order_by(Application.created_at.desc())
    ).all()

    result: list[RecruiterApplicationRead] = []
    for application in rows:
        profile: JobSeekerProfile | None = application.job_seeker.job_seeker_profile
        result.append(
            RecruiterApplicationRead(
                id=application.id,
                job_seeker_id=application.job_seeker_id,
                job_id=application.job_id,
                resume_pdf_url=application.resume_pdf_url,
                github_url=application.github_url,
                status=application.status,
                admin_status=application.admin_status,
                admin_note=application.admin_note,
                chat_thread_id=application.chat_thread_id,
                chat_status=application.chat_status,
                created_at=application.created_at,
                updated_at=application.updated_at,
                job=application.job,
                applicant_name=application.job_seeker.name,
                applicant_email=application.job_seeker.email,
                applicant_github_url=(profile.github_url if profile else None) or application.github_url,
                applicant_resume_pdf_url=(profile.resume_pdf_url if profile else None) or application.resume_pdf_url,
                job_title=application.job.title,
            )
        )
    return result


@router.put("/applications/{application_id}/status", response_model=RecruiterApplicationRead)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> RecruiterApplicationRead:
    if payload.status not in {ApplicationStatus.VIEWED, ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recruiters can only mark viewed, shortlisted, or rejected")

    application = db.scalar(
        select(Application)
        .join(Job)
        .options(
            joinedload(Application.job),
            joinedload(Application.chat_thread),
            joinedload(Application.job_seeker).joinedload(User.job_seeker_profile),
        )
        .where(Application.id == application_id)
        .where(Job.recruiter_id == current_user.id)
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application.status == ApplicationStatus.WITHDRAWN.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Withdrawn applications cannot be updated.")
    if application.admin_status == ApplicationAdminStatus.PAUSED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This application is paused by admin")

    old_status = application.status
    application.status = payload.status.value
    add_timeline_event(
        db,
        application.id,
        payload.status.value,
        old_status=old_status,
        new_status=payload.status.value,
        note=f"Recruiter updated application status to {payload.status.value}",
        created_by_user_id=current_user.id,
    )
    notification_type = (
        "APPLICATION_SHORTLISTED"
        if payload.status == ApplicationStatus.SHORTLISTED
        else "APPLICATION_REJECTED"
        if payload.status == ApplicationStatus.REJECTED
        else "APPLICATION_STATUS_CHANGED"
    )
    create_notification(
        db,
        application.job_seeker_id,
        f"Application {payload.status.value.lower()}",
        f"Your application for {application.job.title} is now {payload.status.value}.",
        notification_type,
        "/jobseeker/applications",
    )
    db.commit()
    db.refresh(application)
    profile = application.job_seeker.job_seeker_profile
    return RecruiterApplicationRead(
        id=application.id,
        job_seeker_id=application.job_seeker_id,
        job_id=application.job_id,
        resume_pdf_url=application.resume_pdf_url,
        github_url=application.github_url,
        status=application.status,
        admin_status=application.admin_status,
        admin_note=application.admin_note,
        chat_thread_id=application.chat_thread_id,
        chat_status=application.chat_status,
        created_at=application.created_at,
        updated_at=application.updated_at,
        job=application.job,
        applicant_name=application.job_seeker.name,
        applicant_email=application.job_seeker.email,
        applicant_github_url=(profile.github_url if profile else None) or application.github_url,
        applicant_resume_pdf_url=(profile.resume_pdf_url if profile else None) or application.resume_pdf_url,
        job_title=application.job.title,
    )
