from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.application import Application
from app.models.company import Company
from app.core.config import settings
from app.models.enums import AccountStatus, CompanyVerificationStatus, JobModerationStatus, JobSeekerDocumentType, RecruiterVerificationStatus, UserRole
from app.models.job import Job
from app.models.job_seeker_document import JobSeekerDocument
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.recruiter_profile import RecruiterProfile
from app.models.swipe import Swipe
from app.models.user import User
from app.schemas.profile import JobSeekerDocumentRead, JobSeekerProfileRead, JobSeekerProfileUpdate, UploadResponse
from app.utils.file_upload import save_image, save_jobseeker_document, save_resume_pdf

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
        academic_status=profile.academic_status,
        degree_name=profile.degree_name,
        stream_or_branch=profile.stream_or_branch,
        college_or_university=profile.college_or_university,
        admission_year=profile.admission_year,
        expected_graduation_year=profile.expected_graduation_year,
        current_year=profile.current_year,
        current_semester=profile.current_semester,
        current_cgpa=profile.current_cgpa,
        internship_preference=profile.internship_preference,
        preferred_internship_duration=profile.preferred_internship_duration,
        available_from=profile.available_from,
        open_to_remote=profile.open_to_remote,
        open_to_relocation=profile.open_to_relocation,
        final_cgpa_or_percentage=profile.final_cgpa_or_percentage,
        looking_for=profile.looking_for,
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
        profile.academic_status,
        profile.degree_name,
        profile.stream_or_branch,
        profile.college_or_university,
    ]
    completion = round(sum(1 for value in fields if value) / len(fields) * 100)

    viewed_jobs = select(Swipe.job_id).where(Swipe.job_seeker_id == current_user.id)
    recommended_count = db.scalar(
        select(func.count(Job.id))
        .join(RecruiterProfile, Job.recruiter_id == RecruiterProfile.user_id)
        .join(Company, Job.company_id == Company.id)
        .join(User, Job.recruiter_id == User.id)
        .where(Job.is_active.is_(True))
        .where(Job.deadline >= date.today())
        .where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
        .where(Job.company_id == RecruiterProfile.company_id)
        .where(RecruiterProfile.recruiter_verification_status == RecruiterVerificationStatus.VERIFIED.value)
        .where(Company.verification_status == CompanyVerificationStatus.VERIFIED.value)
        .where(User.account_status == AccountStatus.ACTIVE.value)
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
    documents = db.scalars(select(JobSeekerDocument).where(JobSeekerDocument.job_seeker_id == current_user.id)).all()
    document_types = {document.document_type for document in documents}
    return {
        "name": current_user.name,
        "profile_completion": completion,
        "recommended_jobs_count": recommended_count or 0,
        "saved_jobs_count": saved_count or 0,
        "applications_count": applications_count or 0,
        "academic_profile_completed": bool(profile.academic_status and profile.degree_name and profile.stream_or_branch),
        "resume_uploaded": bool(profile.resume_pdf_url or "RESUME" in document_types),
        "marksheet_uploaded": "MARKSHEET" in document_types,
        "certificate_uploaded": bool({"CERTIFICATE", "INTERNSHIP_CERTIFICATE", "COURSE_CERTIFICATE"}.intersection(document_types)),
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
    for key, value in payload.model_dump(mode="json").items():
        if key == "skills_list":
            continue
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


@router.get("/documents", response_model=list[JobSeekerDocumentRead])
def list_documents(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[JobSeekerDocument]:
    return list(
        db.scalars(
            select(JobSeekerDocument)
            .where(JobSeekerDocument.job_seeker_id == current_user.id)
            .order_by(JobSeekerDocument.uploaded_at.desc(), JobSeekerDocument.id.desc())
        ).all()
    )


@router.post("/documents", response_model=JobSeekerDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
    document_type: str = Form(...),
    title: str = Form(...),
    related_skill: str | None = Form(default=None),
    issuing_organization: str | None = Form(default=None),
    issue_date: str | None = Form(default=None),
    credential_url: str | None = Form(default=None),
    file: UploadFile = File(...),
) -> JobSeekerDocument:
    try:
        normalized_type = JobSeekerDocumentType(document_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document type.") from exc

    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document title is required.")

    parsed_issue_date: date | None = None
    if issue_date and issue_date.strip():
        try:
            parsed_issue_date = date.fromisoformat(issue_date.strip())
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Issue date must be a valid date.") from exc

    metadata = await save_jobseeker_document(file, resume_only=normalized_type == JobSeekerDocumentType.RESUME)
    document = JobSeekerDocument(
        job_seeker_id=current_user.id,
        document_type=normalized_type.value,
        title=clean_title[:180],
        file_url=str(metadata["url"]),
        original_filename=str(metadata["original_filename"]),
        stored_filename=str(metadata["stored_filename"]),
        mime_type=str(metadata["mime_type"]),
        file_size=int(metadata["file_size"]),
        related_skill=(related_skill or "").strip()[:120] or None,
        issuing_organization=(issuing_organization or "").strip()[:180] or None,
        issue_date=parsed_issue_date,
        credential_url=(credential_url or "").strip()[:500] or None,
        uploaded_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(document)
    if normalized_type == JobSeekerDocumentType.RESUME:
        profile = get_or_create_profile(db, current_user.id)
        profile.resume_pdf_url = document.file_url
    db.commit()
    db.refresh(document)
    return document


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    document = db.scalar(
        select(JobSeekerDocument)
        .where(JobSeekerDocument.id == document_id)
        .where(JobSeekerDocument.job_seeker_id == current_user.id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.document_type == JobSeekerDocumentType.RESUME.value:
        profile = get_or_create_profile(db, current_user.id)
        if profile.resume_pdf_url == document.file_url:
            profile.resume_pdf_url = None
    file_path = (settings.upload_path / "jobseeker-documents" / document.stored_filename).resolve()
    document_root = (settings.upload_path / "jobseeker-documents").resolve()
    db.delete(document)
    db.commit()
    try:
        file_path.relative_to(document_root)
        if file_path.is_file():
            file_path.unlink()
    except ValueError:
        pass
    return {"message": "Document deleted"}
