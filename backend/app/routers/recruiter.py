from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.application import Application
from app.models.company import Company
from app.models.enums import (
    ApplicationAdminStatus,
    ApplicationStatus,
    CompanyVerificationStatus,
    JobModerationStatus,
    RecruiterVerificationStatus,
    UserRole,
)
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User
from app.schemas.application import ApplicationStatusUpdate, RecruiterApplicationRead
from app.schemas.job import JobRead
from app.schemas.profile import CompanyProfileRead, CompanyProfileUpdate, UploadResponse
from app.services.notifications import create_notification
from app.services.timeline import add_timeline_event
from app.utils.file_upload import save_image
from app.utils.pagination import LimitQuery, PageQuery, pagination_offset

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


def get_or_create_recruiter_profile(db: Session, user: User) -> RecruiterProfile:
    profile = db.scalar(
        select(RecruiterProfile)
        .options(joinedload(RecruiterProfile.company))
        .where(RecruiterProfile.user_id == user.id)
    )
    if profile is None:
        company = Company(company_name=f"{user.name}'s Company", verification_status=CompanyVerificationStatus.PENDING.value)
        db.add(company)
        db.flush()
        profile = RecruiterProfile(user_id=user.id, company_id=company.id, official_email=user.email)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    elif profile.company is None:
        company = Company(company_name=f"{user.name}'s Company", verification_status=CompanyVerificationStatus.PENDING.value)
        db.add(company)
        db.flush()
        profile.company_id = company.id
        db.commit()
        db.refresh(profile)
    return profile


def company_profile_response(profile: RecruiterProfile) -> CompanyProfileRead:
    company = profile.company
    return CompanyProfileRead(
        id=profile.id,
        recruiter_id=profile.user_id,
        company_id=profile.company_id,
        company_name=company.company_name if company else None,
        company_logo_url=company.company_logo_url if company else None,
        company_type=company.company_type if company else None,
        industry=company.industry if company else None,
        website=company.website if company else None,
        official_email_domain=company.official_email_domain if company else None,
        description=company.description if company else None,
        headquarters_location=company.headquarters_location if company else None,
        location=company.headquarters_location if company else None,
        founded_year=company.founded_year if company else None,
        company_size=company.company_size if company else None,
        registration_number=company.registration_number if company else None,
        verification_status=company.verification_status if company else CompanyVerificationStatus.PENDING.value,
        company_verification_note=company.verification_note if company else None,
        company_verified_at=company.verified_at if company else None,
        company_verified_by_admin_id=company.verified_by_admin_id if company else None,
        average_rating=company.average_rating if company else 0,
        total_reviews=company.total_reviews if company else 0,
        designation=profile.designation,
        department=profile.department,
        official_email=profile.official_email,
        recruiter_verification_status=profile.recruiter_verification_status,
        verification_note=profile.verification_note,
        verified_at=profile.verified_at,
        verified_by_admin_id=profile.verified_by_admin_id,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


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
    profile = get_or_create_recruiter_profile(db, current_user)
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "expired_jobs": expired_jobs,
        "applications_received": applications,
        "posted_jobs": [JobRead.model_validate(job).model_dump(mode="json") for job in jobs],
        "company_profile": company_profile_response(profile).model_dump(mode="json"),
    }


@router.get("/company-profile", response_model=CompanyProfileRead)
def get_company_profile(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyProfileRead:
    return company_profile_response(get_or_create_recruiter_profile(db, current_user))


@router.put("/company-profile", response_model=CompanyProfileRead)
def update_company_profile(
    payload: CompanyProfileUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyProfileRead:
    profile = get_or_create_recruiter_profile(db, current_user)
    payload_data = payload.model_dump(exclude_unset=True)

    if payload_data.get("company_id") and payload_data["company_id"] != profile.company_id:
        company = db.get(Company, payload_data["company_id"])
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        profile.company_id = company.id
        profile.recruiter_verification_status = RecruiterVerificationStatus.PENDING.value
        profile.verification_note = "Recruiter requested to join this company."
        profile.verified_at = None
        profile.verified_by_admin_id = None
    else:
        company = profile.company
        if company is None:
            company = Company(company_name=f"{current_user.name}'s Company", verification_status=CompanyVerificationStatus.PENDING.value)
            db.add(company)
            db.flush()
            profile.company_id = company.id
        company_fields = {
            "company_name",
            "company_type",
            "industry",
            "website",
            "official_email_domain",
            "description",
            "headquarters_location",
            "founded_year",
            "company_size",
            "registration_number",
        }
        changed_company = False
        for key in company_fields:
            value = payload_data.get(key)
            if key == "headquarters_location" and value is None:
                value = payload_data.get("location")
            if key in payload_data or (key == "headquarters_location" and "location" in payload_data):
                setattr(company, key, value)
                changed_company = True
        if changed_company and company.verification_status == CompanyVerificationStatus.REJECTED.value:
            company.verification_status = CompanyVerificationStatus.PENDING.value
            company.verified_at = None
            company.verified_by_admin_id = None

    for key in {"designation", "department", "official_email"}:
        if key in payload_data:
            setattr(profile, key, payload_data[key])
    if profile.recruiter_verification_status == RecruiterVerificationStatus.REJECTED.value:
        profile.recruiter_verification_status = RecruiterVerificationStatus.PENDING.value
        profile.verified_at = None
        profile.verified_by_admin_id = None
    db.commit()
    db.refresh(profile)
    return company_profile_response(profile)


@router.post("/company-logo", response_model=UploadResponse)
async def upload_company_logo(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> UploadResponse:
    profile = get_or_create_recruiter_profile(db, current_user)
    company = profile.company
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    url = await save_image(file, "company-logos")
    company.company_logo_url = url
    db.commit()
    return UploadResponse(url=url, message="Company logo uploaded")


@router.get("/applications", response_model=list[RecruiterApplicationRead])
def applications(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[RecruiterApplicationRead]:
    statement = (
        select(Application)
        .join(Job)
        .join(User, Application.job_seeker_id == User.id)
        .options(
            joinedload(Application.job),
            joinedload(Application.chat_thread),
            joinedload(Application.job_seeker).joinedload(User.job_seeker_profile),
        )
        .where(Job.recruiter_id == current_user.id)
        .order_by(Application.created_at.desc())
    )
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Job.title.ilike(term), User.name.ilike(term), User.email.ilike(term)))
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    rows = db.scalars(statement).all()

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
