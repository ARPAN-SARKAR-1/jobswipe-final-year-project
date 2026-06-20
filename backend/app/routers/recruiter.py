from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.application import Application
from app.models.company_profile import CompanyProfile
from app.models.company_testimonial import CompanyTestimonial
from app.models.enums import ApplicationAdminStatus, ApplicationStatus, CompanyJoinStatus, JobModerationStatus, RecruiterVerificationStatus, SectionVisibility, UserRole
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.user import User
from app.schemas.application import ApplicationStatusUpdate, RecruiterApplicationRead
from app.schemas.company import CompanyTestimonialCreate, CompanyTestimonialRead, CompanyTestimonialUpdate
from app.schemas.job import JobRead
from app.schemas.profile import CompanyJoinRequest, CompanyProfileRead, CompanyProfileUpdate, UploadResponse
from app.services.notifications import create_notification, notify_admins
from app.services.profile_requirements import check_company_profile_completion, validate_http_url
from app.services.public_identity import ensure_company_public_identity, unique_company_slug
from app.services.timeline import add_timeline_event
from app.services.trust import attach_job_trust, get_or_create_recruiter_membership, get_recruiter_membership
from app.utils.file_upload import save_company_logo

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


def applicant_accessibility_payload(profile: JobSeekerProfile | None) -> dict[str, str | bool | None]:
    if not profile or not profile.has_accessibility_needs:
        return {
            "applicant_has_accessibility_needs": None,
            "applicant_accessibility_needs": None,
            "applicant_accessibility_notes": None,
            "applicant_accessibility_visibility": None,
        }
    if profile.accessibility_visibility not in {SectionVisibility.PUBLIC.value, SectionVisibility.RECRUITERS_ONLY.value}:
        return {
            "applicant_has_accessibility_needs": None,
            "applicant_accessibility_needs": None,
            "applicant_accessibility_notes": None,
            "applicant_accessibility_visibility": None,
        }
    return {
        "applicant_has_accessibility_needs": True,
        "applicant_accessibility_needs": profile.accessibility_needs,
        "applicant_accessibility_notes": profile.accessibility_notes,
        "applicant_accessibility_visibility": profile.accessibility_visibility,
    }


def get_or_create_company(db: Session, recruiter_id: int) -> CompanyProfile:
    membership = get_recruiter_membership(db, recruiter_id)
    if membership and membership.company:
        return membership.company
    company = db.scalar(select(CompanyProfile).where(CompanyProfile.recruiter_id == recruiter_id))
    if company is None:
        company = CompanyProfile(recruiter_id=recruiter_id)
        db.add(company)
        db.flush()
    recruiter = db.get(User, recruiter_id)
    if recruiter:
        get_or_create_recruiter_membership(db, recruiter, company)
    ensure_company_public_identity(db, company)
    db.commit()
    db.refresh(company)
    return company


def company_profile_response(db: Session, company: CompanyProfile, recruiter: User | None = None) -> CompanyProfileRead:
    profile_user = recruiter or company.recruiter
    membership = get_or_create_recruiter_membership(db, profile_user, company) if profile_user else None
    completion = check_company_profile_completion(company, membership)
    return CompanyProfileRead(
        id=company.id,
        public_company_id=company.public_company_id,
        slug=company.slug,
        recruiter_id=profile_user.id if profile_user else company.recruiter_id,
        company_name=company.company_name,
        name=company.company_name,
        company_logo_url=company.company_logo_url,
        logo_url=company.company_logo_url,
        website=company.website,
        industry=company.industry,
        company_size=company.company_size,
        employee_count_estimate=company.employee_count_estimate,
        headquarters=company.headquarters,
        founded_year=company.founded_year,
        company_type=company.company_type,
        description=company.description,
        location=company.location,
        career_page_url=company.career_page_url,
        linkedin_url=company.linkedin_url,
        glassdoor_url=company.glassdoor_url,
        ambitionbox_url=company.ambitionbox_url,
        about_company=company.about_company,
        culture_summary=company.culture_summary,
        benefits=company.benefits,
        hiring_process=company.hiring_process,
        work_mode=company.work_mode,
        rating_source=company.rating_source,
        official_email_domain=company.official_email_domain,
        verification_status=company.verification_status,
        recruiter_verification_status=(membership.verification_status if membership else company.recruiter_verification_status),
        company_join_status=(membership.company_join_status if membership else CompanyJoinStatus.PENDING.value),
        designation=(membership.designation if membership else None),
        work_email=(membership.work_email if membership else None),
        verification_note=company.verification_note,
        company_completion_percentage=completion.completion_percentage,
        missing_company_fields=completion.missing_fields,
        verified_at=company.verified_at,
        verified_by_admin_id=company.verified_by_admin_id,
        created_at=company.created_at,
        updated_at=company.updated_at,
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
    company = get_or_create_company(db, current_user.id)
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "expired_jobs": expired_jobs,
        "applications_received": applications,
        "posted_jobs": [JobRead.model_validate(attach_job_trust(db, job)).model_dump(mode="json") for job in jobs],
        "company_profile": company_profile_response(db, company, current_user).model_dump(mode="json"),
    }


@router.get("/company-profile", response_model=CompanyProfileRead)
def get_company_profile(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyProfileRead:
    return company_profile_response(db, get_or_create_company(db, current_user.id), current_user)


@router.put("/company-profile", response_model=CompanyProfileRead)
def update_company_profile(
    payload: CompanyProfileUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyProfileRead:
    company = get_or_create_company(db, current_user.id)
    membership = get_or_create_recruiter_membership(db, current_user, company)
    update_data = payload.model_dump()
    for url_field, label in {
        "website": "Company website",
        "career_page_url": "Career page URL",
        "linkedin_url": "LinkedIn URL",
        "glassdoor_url": "Glassdoor URL",
        "ambitionbox_url": "AmbitionBox URL",
    }.items():
        if update_data.get(url_field):
            validate_http_url(update_data[url_field], label)
    member_fields = {"designation", "work_email"}
    for key, value in update_data.items():
        if value is None:
            continue
        if key in member_fields:
            setattr(membership, key, value)
            continue
        if company.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the company owner can update company details.",
            )
        setattr(company, key, value)
    if company.official_email_domain is None and membership.work_email and "@" in membership.work_email:
        company.official_email_domain = membership.work_email.split("@", 1)[1].lower()
    company.recruiter_verification_status = membership.verification_status
    ensure_company_public_identity(db, company)
    if company.company_name and company.slug in {None, "company"}:
        company.slug = unique_company_slug(db, company.company_name)
    db.commit()
    db.refresh(company)
    return company_profile_response(db, company, current_user)


def testimonial_response(testimonial: CompanyTestimonial) -> CompanyTestimonialRead:
    return CompanyTestimonialRead.model_validate(testimonial)


@router.get("/company-testimonials", response_model=list[CompanyTestimonialRead])
def list_company_testimonials(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[CompanyTestimonialRead]:
    company = get_or_create_company(db, current_user.id)
    testimonials = db.scalars(
        select(CompanyTestimonial)
        .where(CompanyTestimonial.company_id == company.id)
        .order_by(CompanyTestimonial.created_at.desc(), CompanyTestimonial.id.desc())
    ).all()
    return [testimonial_response(testimonial) for testimonial in testimonials]


@router.post("/company-testimonials", response_model=CompanyTestimonialRead, status_code=status.HTTP_201_CREATED)
def create_company_testimonial(
    payload: CompanyTestimonialCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyTestimonialRead:
    company = get_or_create_company(db, current_user.id)
    if company.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the company owner can add company testimonials.")
    testimonial = CompanyTestimonial(
        company_id=company.id,
        created_by_user_id=current_user.id,
        title=payload.title.strip(),
        statement=payload.statement.strip(),
        reviewer_label=payload.reviewer_label.strip() if payload.reviewer_label else None,
        rating=payload.rating,
        visibility=payload.visibility.value,
    )
    db.add(testimonial)
    notify_admins(
        db,
        "Company testimonial pending review",
        f"{company.company_name or 'A company'} submitted a company-provided testimonial.",
        "COMPANY_VERIFICATION",
        "/admin/dashboard",
    )
    db.commit()
    db.refresh(testimonial)
    return testimonial_response(testimonial)


@router.patch("/company-testimonials/{testimonial_id}", response_model=CompanyTestimonialRead)
def update_company_testimonial(
    testimonial_id: int,
    payload: CompanyTestimonialUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyTestimonialRead:
    company = get_or_create_company(db, current_user.id)
    if company.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the company owner can update company testimonials.")
    testimonial = db.scalar(
        select(CompanyTestimonial)
        .where(CompanyTestimonial.id == testimonial_id)
        .where(CompanyTestimonial.company_id == company.id)
    )
    if testimonial is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company testimonial not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(testimonial, key, value.value if hasattr(value, "value") else value)
    testimonial.status = "PENDING_ADMIN_REVIEW"
    testimonial.admin_note = None
    testimonial.reviewed_by = None
    testimonial.reviewed_at = None
    db.commit()
    db.refresh(testimonial)
    return testimonial_response(testimonial)


@router.post("/company-membership/request", response_model=CompanyProfileRead)
def request_company_membership(
    payload: CompanyJoinRequest,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyProfileRead:
    company = db.get(CompanyProfile, payload.company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    membership = get_recruiter_membership(db, current_user.id)
    if membership and membership.company_id != company.id:
        if (
            membership.company_join_status == CompanyJoinStatus.APPROVED.value
            and membership.verification_status == RecruiterVerificationStatus.VERIFIED.value
        ):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already belong to a verified company.")
        membership.company_id = company.id
    elif membership is None:
        membership = get_or_create_recruiter_membership(db, current_user, company)
    if membership.verification_status == RecruiterVerificationStatus.SUSPENDED.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suspended recruiters cannot request company membership.")
    membership.designation = payload.designation
    membership.work_email = payload.work_email
    membership.company_join_status = CompanyJoinStatus.PENDING.value
    membership.verification_status = RecruiterVerificationStatus.PENDING.value
    membership.verified_at = None
    membership.verified_by_admin_id = None
    membership.verified_by_company_owner_id = None
    membership.admin_note = None
    notify_admins(
        db,
        "Recruiter membership requested",
        f"{current_user.name} requested to join {company.company_name or 'a company'}.",
        "RECRUITER_VERIFICATION",
        "/admin/dashboard",
    )
    db.commit()
    db.refresh(company)
    return company_profile_response(db, company, current_user)


@router.post("/company-logo", response_model=UploadResponse)
async def upload_company_logo(
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> UploadResponse:
    company = get_or_create_company(db, current_user.id)
    if company.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the company owner can update the company logo.")
    url = await save_company_logo(file)
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
                applicant_job_seeker_category=profile.job_seeker_category if profile else None,
                applicant_student_verification_status=profile.student_verification_status if profile else None,
                applicant_graduation_verification_status=profile.graduation_verification_status if profile else None,
                applicant_experience_verification_status=profile.experience_verification_status if profile else None,
                applicant_passing_year=(profile.expected_passing_year or profile.graduation_year or profile.passing_year) if profile else None,
                applicant_total_experience_years=profile.total_experience_years if profile else None,
                job_title=application.job.title,
                **applicant_accessibility_payload(profile),
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
        applicant_job_seeker_category=profile.job_seeker_category if profile else None,
        applicant_student_verification_status=profile.student_verification_status if profile else None,
        applicant_graduation_verification_status=profile.graduation_verification_status if profile else None,
        applicant_experience_verification_status=profile.experience_verification_status if profile else None,
        applicant_passing_year=(profile.expected_passing_year or profile.graduation_year or profile.passing_year) if profile else None,
        applicant_total_experience_years=profile.total_experience_years if profile else None,
        job_title=application.job.title,
        **applicant_accessibility_payload(profile),
    )
