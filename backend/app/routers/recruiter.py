from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.application import Application
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.enums import (
    ApplicationAdminStatus,
    ApplicationStatus,
    CompanyVerificationStatus,
    CompanyMemberRole,
    JobModerationStatus,
    RecruiterVerificationStatus,
    UserRole,
)
from app.models.job import Job
from app.models.job_seeker_document import JobSeekerDocument
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.recruiter_profile import RecruiterProfile
from app.models.user import User
from app.schemas.application import ApplicationStatusUpdate, CandidateReportCreate, RecruiterApplicationRead
from app.schemas.job import JobRead
from app.schemas.profile import CompanyProfileRead, CompanyProfileUpdate, UploadResponse
from app.services.notifications import create_notification
from app.services.company_claims import ensure_company_member, find_company_by_normalized_name
from app.services.risk_assessment import assess_candidate_risk
from app.services.recruiter_reviews import recruiter_review_summary
from app.services.user_risk_assessment import update_user_risk
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
    if profile.company_id:
        ensure_company_member(
            db,
            profile.company_id,
            user.id,
            CompanyMemberRole.COMPANY_RECRUITER.value,
            profile.recruiter_verification_status,
            "Synced from recruiter profile.",
        )
        db.commit()
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
        "recruiter_review_summary": recruiter_review_summary(db, current_user.id),
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
        if company.verification_status == CompanyVerificationStatus.VERIFIED.value:
            ensure_company_member(
                db,
                company.id,
                current_user.id,
                CompanyMemberRole.COMPANY_RECRUITER.value,
                RecruiterVerificationStatus.PENDING.value,
                "Recruiter requested to join this verified company.",
            )
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
                if key == "company_name" and value and company.verification_status != CompanyVerificationStatus.VERIFIED.value:
                    duplicate = find_company_by_normalized_name(db, value)
                    if duplicate and duplicate.id != company.id and duplicate.verification_status == CompanyVerificationStatus.VERIFIED.value:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="A verified company with this name already exists. Request to join that company instead.",
                        )
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
    academic_status: str | None = None,
    degree: str | None = None,
    stream: str | None = None,
    graduation_year: int | None = None,
    current_year: str | None = None,
    min_cgpa: float | None = None,
    skills: str | None = None,
    certificates_available: bool | None = None,
) -> list[RecruiterApplicationRead]:
    statement = (
        select(Application)
        .join(Job)
        .join(User, Application.job_seeker_id == User.id)
        .outerjoin(JobSeekerProfile, JobSeekerProfile.user_id == Application.job_seeker_id)
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
        statement = statement.where(
            or_(
                Job.title.ilike(term),
                User.name.ilike(term),
                User.email.ilike(term),
                JobSeekerProfile.degree_name.ilike(term),
                JobSeekerProfile.stream_or_branch.ilike(term),
                JobSeekerProfile.skills.ilike(term),
            )
        )
    if academic_status:
        statement = statement.where(JobSeekerProfile.academic_status == academic_status)
    if degree:
        statement = statement.where(or_(JobSeekerProfile.degree_name.ilike(f"%{degree.strip()}%"), JobSeekerProfile.degree.ilike(f"%{degree.strip()}%")))
    if stream:
        statement = statement.where(JobSeekerProfile.stream_or_branch.ilike(f"%{stream.strip()}%"))
    if graduation_year:
        statement = statement.where(or_(JobSeekerProfile.expected_graduation_year == graduation_year, JobSeekerProfile.passing_year == graduation_year))
    if current_year:
        statement = statement.where(JobSeekerProfile.current_year == current_year)
    if min_cgpa is not None:
        statement = statement.where(JobSeekerProfile.current_cgpa >= min_cgpa)
    if skills:
        statement = statement.where(JobSeekerProfile.skills.ilike(f"%{skills.strip()}%"))
    if certificates_available is True:
        document_seekers = select(JobSeekerDocument.job_seeker_id).where(
            JobSeekerDocument.document_type.in_(["CERTIFICATE", "INTERNSHIP_CERTIFICATE", "COURSE_CERTIFICATE"])
        )
        statement = statement.where(Application.job_seeker_id.in_(document_seekers))
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    rows = db.scalars(statement).all()

    result: list[RecruiterApplicationRead] = []
    for application in rows:
        profile: JobSeekerProfile | None = application.job_seeker.job_seeker_profile
        documents = list(
            db.scalars(
                select(JobSeekerDocument)
                .where(JobSeekerDocument.job_seeker_id == application.job_seeker_id)
                .order_by(JobSeekerDocument.uploaded_at.desc(), JobSeekerDocument.id.desc())
            ).all()
        )
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
                applicant_academic_status=profile.academic_status if profile else None,
                applicant_degree_name=(profile.degree_name or profile.degree) if profile else None,
                applicant_stream_or_branch=profile.stream_or_branch if profile else None,
                applicant_college_or_university=(profile.college_or_university or profile.college) if profile else None,
                applicant_graduation_year=(profile.expected_graduation_year or profile.passing_year) if profile else None,
                applicant_current_year=profile.current_year if profile else None,
                applicant_cgpa=profile.current_cgpa if profile else None,
                applicant_experience_level=profile.experience_level if profile else None,
                applicant_internship_preference=profile.internship_preference if profile else None,
                applicant_open_to_remote=profile.open_to_remote if profile else False,
                applicant_open_to_relocation=profile.open_to_relocation if profile else False,
                applicant_skills=profile.skills if profile else None,
                applicant_documents=documents,
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
    update_user_risk(db, application.job_seeker)
    db.commit()
    db.refresh(application)
    profile = application.job_seeker.job_seeker_profile
    documents = list(
        db.scalars(
            select(JobSeekerDocument)
            .where(JobSeekerDocument.job_seeker_id == application.job_seeker_id)
            .order_by(JobSeekerDocument.uploaded_at.desc(), JobSeekerDocument.id.desc())
        ).all()
    )
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
        applicant_academic_status=profile.academic_status if profile else None,
        applicant_degree_name=(profile.degree_name or profile.degree) if profile else None,
        applicant_stream_or_branch=profile.stream_or_branch if profile else None,
        applicant_college_or_university=(profile.college_or_university or profile.college) if profile else None,
        applicant_graduation_year=(profile.expected_graduation_year or profile.passing_year) if profile else None,
        applicant_current_year=profile.current_year if profile else None,
        applicant_cgpa=profile.current_cgpa if profile else None,
        applicant_experience_level=profile.experience_level if profile else None,
        applicant_internship_preference=profile.internship_preference if profile else None,
        applicant_open_to_remote=profile.open_to_remote if profile else False,
        applicant_open_to_relocation=profile.open_to_relocation if profile else False,
        applicant_skills=profile.skills if profile else None,
        applicant_documents=documents,
        job_title=application.job.title,
    )


@router.post("/applications/{application_id}/report-candidate")
def report_candidate(
    application_id: int,
    payload: CandidateReportCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    application = db.scalar(
        select(Application)
        .join(Job)
        .options(joinedload(Application.job_seeker), joinedload(Application.job))
        .where(Application.id == application_id)
        .where(Job.recruiter_id == current_user.id)
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    assess_candidate_risk(db, application.job_seeker, payload.reason)
    create_notification(
        db,
        application.job_seeker_id,
        "Application reviewed",
        "A recruiter submitted feedback for admin review.",
        "CANDIDATE_REPORTED",
        "/jobseeker/applications",
    )
    update_user_risk(db, application.job_seeker)
    db.commit()
    return {"message": "Candidate report submitted for admin review."}
