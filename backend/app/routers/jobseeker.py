from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.application import Application
from app.models.enums import JobModerationStatus, SectionVisibility, UserRole
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.job_seeker_recommendation import JobSeekerRecommendation
from app.models.job_seeker_reference import JobSeekerReference
from app.models.swipe import Swipe
from app.models.user import User
from app.models.user_document import UserDocument
from app.schemas.profile import (
    JobSeekerCategoryUpdate,
    JobSeekerProfileRead,
    JobSeekerProfileUpdate,
    JobSeekerRecommendationCreate,
    JobSeekerRecommendationRead,
    JobSeekerRecommendationUpdate,
    JobSeekerReferenceCreate,
    JobSeekerReferenceRead,
    JobSeekerReferenceUpdate,
    UploadResponse,
)
from app.schemas.public_profile import DocumentVisibilityUpdate, UserDocumentRead
from app.services.public_identity import ensure_user_public_identity
from app.utils.file_upload import save_profile_photo, save_resume_pdf, save_verification_document

router = APIRouter(prefix="/jobseeker", tags=["Job Seeker"])

JOB_SEEKER_DOCUMENT_TYPES = {
    "resume",
    "marksheet_10",
    "marksheet_12",
    "diploma",
    "graduation",
    "post_graduation",
    "certificate",
    "college_id_card",
    "library_card",
    "bonafide_certificate",
    "admission_proof",
    "fee_receipt",
    "graduation_marksheet",
    "degree_certificate",
    "provisional_certificate",
    "experience_letter",
    "relieving_letter",
    "offer_letter",
    "salary_slip",
    "recommendation_letter",
    "reference_letter",
    "other",
}
PRIVATE_ONLY_DOCUMENT_TYPES = {
    "resume",
    "marksheet_10",
    "marksheet_12",
    "diploma",
    "graduation",
    "post_graduation",
    "college_id_card",
    "library_card",
    "bonafide_certificate",
    "admission_proof",
    "fee_receipt",
    "graduation_marksheet",
    "degree_certificate",
    "provisional_certificate",
    "experience_letter",
    "relieving_letter",
    "offer_letter",
    "salary_slip",
    "reference_letter",
}


def get_or_create_profile(db: Session, user_id: int) -> JobSeekerProfile:
    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == user_id))
    if profile is None:
        profile = JobSeekerProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def normalize_visibility(value: str | SectionVisibility | None, *, allow_public: bool = True) -> str:
    raw_value = value.value if isinstance(value, SectionVisibility) else value
    normalized = (raw_value or SectionVisibility.PRIVATE.value).strip().upper()
    allowed = {item.value for item in SectionVisibility}
    if not allow_public:
        allowed.discard(SectionVisibility.PUBLIC.value)
    if normalized not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported visibility value.")
    return normalized


def document_response(document: UserDocument, include_file_url: bool = True) -> UserDocumentRead:
    return UserDocumentRead(
        id=document.id,
        owner_user_id=document.owner_user_id,
        document_type=document.document_type,
        original_filename=document.original_filename,
        is_public=document.is_public,
        visibility=document.visibility,
        verification_status=document.verification_status,
        reviewed_by=document.reviewed_by,
        reviewed_at=document.reviewed_at,
        review_note=document.review_note,
        file_url=document.file_url if include_file_url else None,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def profile_response(profile: JobSeekerProfile, user: User) -> JobSeekerProfileRead:
    return JobSeekerProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        public_user_id=user.public_user_id,
        username=user.username,
        name=user.name,
        email=user.email,
        profile_picture_url=user.profile_picture_url,
        resume_pdf_url=profile.resume_pdf_url,
        phone=profile.phone,
        github_url=profile.github_url,
        about=profile.about or user.bio,
        verification_status=profile.verification_status,
        certificates_public=profile.certificates_public,
        education=profile.education,
        degree=profile.degree,
        college=profile.college,
        passing_year=profile.passing_year,
        cgpa_or_percentage=profile.cgpa_or_percentage,
        skills=profile.skills,
        experience_level=profile.experience_level,
        preferred_location=profile.preferred_location,
        preferred_job_type=profile.preferred_job_type,
        job_seeker_category=profile.job_seeker_category,
        college_name=profile.college_name,
        university_name=profile.university_name,
        course_name=profile.course_name,
        degree_name=profile.degree_name,
        department_or_branch=profile.department_or_branch,
        current_year_or_semester=profile.current_year_or_semester,
        expected_passing_year=profile.expected_passing_year,
        college_location=profile.college_location,
        student_id_number=profile.student_id_number,
        internship_interest=profile.internship_interest,
        preferred_internship_roles=profile.preferred_internship_roles,
        highest_degree=profile.highest_degree,
        graduation_year=profile.graduation_year,
        specialization_or_branch=profile.specialization_or_branch,
        fresher_skills=profile.fresher_skills,
        certifications=profile.certifications,
        project_links=profile.project_links,
        internship_experience=profile.internship_experience,
        preferred_job_roles=profile.preferred_job_roles,
        total_experience_years=profile.total_experience_years,
        current_or_last_company=profile.current_or_last_company,
        current_or_last_role=profile.current_or_last_role,
        employment_type=profile.employment_type,
        notice_period=profile.notice_period,
        previous_companies=profile.previous_companies,
        role_history=profile.role_history,
        key_responsibilities=profile.key_responsibilities,
        tools_technologies=profile.tools_technologies,
        achievements=profile.achievements,
        preferred_next_roles=profile.preferred_next_roles,
        education_visibility=profile.education_visibility,
        experience_visibility=profile.experience_visibility,
        recommendation_visibility=profile.recommendation_visibility,
        reference_visibility=profile.reference_visibility,
        certificate_visibility=profile.certificate_visibility,
        student_verification_status=profile.student_verification_status,
        graduation_verification_status=profile.graduation_verification_status,
        experience_verification_status=profile.experience_verification_status,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def recommendation_response(recommendation: JobSeekerRecommendation) -> JobSeekerRecommendationRead:
    return JobSeekerRecommendationRead(
        id=recommendation.id,
        title=recommendation.title,
        organization=recommendation.organization,
        issued_by=recommendation.issued_by,
        issue_date=recommendation.issue_date,
        file_url=recommendation.file_url,
        visibility=recommendation.visibility,
        verification_status=recommendation.verification_status,
        reviewed_by=recommendation.reviewed_by,
        reviewed_at=recommendation.reviewed_at,
        review_note=recommendation.review_note,
        created_at=recommendation.created_at,
        updated_at=recommendation.updated_at,
    )


def reference_response(reference: JobSeekerReference) -> JobSeekerReferenceRead:
    return JobSeekerReferenceRead(
        id=reference.id,
        reference_name=reference.reference_name,
        reference_role=reference.reference_role,
        organization=reference.organization,
        relationship=reference.relationship,
        email=reference.email,
        phone=reference.phone,
        visibility=reference.visibility,
        note=reference.note,
        verification_status=reference.verification_status,
        reviewed_by=reference.reviewed_by,
        reviewed_at=reference.reviewed_at,
        review_note=reference.review_note,
        created_at=reference.created_at,
        updated_at=reference.updated_at,
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
    ensure_user_public_identity(db, current_user)
    profile = get_or_create_profile(db, current_user.id)
    db.commit()
    return profile_response(profile, current_user)


@router.put("/profile", response_model=JobSeekerProfileRead)
def update_profile(
    payload: JobSeekerProfileUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerProfileRead:
    profile = get_or_create_profile(db, current_user.id)
    for key, value in payload.model_dump(mode="json").items():
        setattr(profile, key, value)
        if key == "about":
            current_user.bio = value
    ensure_user_public_identity(db, current_user)
    db.commit()
    db.refresh(profile)
    return profile_response(profile, current_user)


def patch_profile_fields(
    payload: JobSeekerProfileUpdate,
    current_user: User,
    db: Session,
) -> JobSeekerProfileRead:
    profile = get_or_create_profile(db, current_user.id)
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(profile, key, value)
        if key == "about":
            current_user.bio = value
    ensure_user_public_identity(db, current_user)
    db.commit()
    db.refresh(profile)
    return profile_response(profile, current_user)


@router.patch("/profile/category", response_model=JobSeekerProfileRead)
def update_profile_category(
    payload: JobSeekerCategoryUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerProfileRead:
    profile = get_or_create_profile(db, current_user.id)
    profile.job_seeker_category = payload.job_seeker_category.value
    db.commit()
    db.refresh(profile)
    return profile_response(profile, current_user)


@router.patch("/profile/education", response_model=JobSeekerProfileRead)
def update_profile_education(
    payload: JobSeekerProfileUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerProfileRead:
    return patch_profile_fields(payload, current_user, db)


@router.patch("/profile/experience", response_model=JobSeekerProfileRead)
def update_profile_experience(
    payload: JobSeekerProfileUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerProfileRead:
    return patch_profile_fields(payload, current_user, db)


@router.post("/profile-picture", response_model=UploadResponse)
async def upload_profile_picture(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> UploadResponse:
    url = await save_profile_photo(file)
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


@router.get("/documents", response_model=list[UserDocumentRead])
def list_documents(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserDocumentRead]:
    documents = db.scalars(
        select(UserDocument).where(UserDocument.owner_user_id == current_user.id).order_by(UserDocument.created_at.desc())
    ).all()
    return [document_response(document, include_file_url=True) for document in documents]


@router.post("/documents", response_model=UserDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
    document_type: Annotated[str, Form(..., min_length=3, max_length=60)],
    file: UploadFile = File(...),
    visibility: Annotated[str, Form()] = SectionVisibility.PRIVATE.value,
) -> UserDocumentRead:
    normalized_type = document_type.strip().lower()
    if normalized_type not in JOB_SEEKER_DOCUMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported document type for this account.")
    requested_visibility = normalize_visibility(visibility)
    final_visibility = SectionVisibility.PRIVATE.value if normalized_type in PRIVATE_ONLY_DOCUMENT_TYPES else requested_visibility
    url = await save_verification_document(file, normalized_type)
    document = UserDocument(
        owner_user_id=current_user.id,
        document_type=normalized_type,
        file_url=url,
        original_filename=file.filename,
        is_public=final_visibility == SectionVisibility.PUBLIC.value,
        visibility=final_visibility,
    )
    db.add(document)
    profile = get_or_create_profile(db, current_user.id)
    if normalized_type == "resume":
        profile.resume_pdf_url = url
    db.commit()
    db.refresh(document)
    return document_response(document, include_file_url=True)


@router.patch("/documents/{document_id}/visibility", response_model=UserDocumentRead)
def update_document_visibility(
    document_id: int,
    payload: DocumentVisibilityUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> UserDocumentRead:
    document = db.scalar(
        select(UserDocument).where(UserDocument.id == document_id).where(UserDocument.owner_user_id == current_user.id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    requested_visibility = normalize_visibility(payload.visibility or (SectionVisibility.PUBLIC.value if payload.is_public else SectionVisibility.PRIVATE.value))
    final_visibility = SectionVisibility.PRIVATE.value if document.document_type in PRIVATE_ONLY_DOCUMENT_TYPES else requested_visibility
    document.visibility = final_visibility
    document.is_public = final_visibility == SectionVisibility.PUBLIC.value
    db.commit()
    db.refresh(document)
    return document_response(document, include_file_url=True)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    document = db.scalar(
        select(UserDocument).where(UserDocument.id == document_id).where(UserDocument.owner_user_id == current_user.id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.delete(document)
    db.commit()


@router.get("/recommendations", response_model=list[JobSeekerRecommendationRead])
def list_recommendations(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[JobSeekerRecommendationRead]:
    profile = get_or_create_profile(db, current_user.id)
    recommendations = db.scalars(
        select(JobSeekerRecommendation)
        .where(JobSeekerRecommendation.profile_id == profile.id)
        .order_by(JobSeekerRecommendation.created_at.desc())
    ).all()
    return [recommendation_response(recommendation) for recommendation in recommendations]


@router.post("/recommendations", response_model=JobSeekerRecommendationRead, status_code=status.HTTP_201_CREATED)
def create_recommendation(
    payload: JobSeekerRecommendationCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerRecommendationRead:
    profile = get_or_create_profile(db, current_user.id)
    recommendation = JobSeekerRecommendation(profile_id=profile.id, **payload.model_dump(mode="json"))
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation_response(recommendation)


@router.patch("/recommendations/{recommendation_id}", response_model=JobSeekerRecommendationRead)
def update_recommendation(
    recommendation_id: int,
    payload: JobSeekerRecommendationUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerRecommendationRead:
    profile = get_or_create_profile(db, current_user.id)
    recommendation = db.scalar(
        select(JobSeekerRecommendation)
        .where(JobSeekerRecommendation.id == recommendation_id)
        .where(JobSeekerRecommendation.profile_id == profile.id)
    )
    if recommendation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(recommendation, key, value)
    db.commit()
    db.refresh(recommendation)
    return recommendation_response(recommendation)


@router.delete("/recommendations/{recommendation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recommendation(
    recommendation_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    profile = get_or_create_profile(db, current_user.id)
    recommendation = db.scalar(
        select(JobSeekerRecommendation)
        .where(JobSeekerRecommendation.id == recommendation_id)
        .where(JobSeekerRecommendation.profile_id == profile.id)
    )
    if recommendation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    db.delete(recommendation)
    db.commit()


@router.get("/references", response_model=list[JobSeekerReferenceRead])
def list_references(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> list[JobSeekerReferenceRead]:
    profile = get_or_create_profile(db, current_user.id)
    references = db.scalars(
        select(JobSeekerReference)
        .where(JobSeekerReference.profile_id == profile.id)
        .order_by(JobSeekerReference.created_at.desc())
    ).all()
    return [reference_response(reference) for reference in references]


@router.post("/references", response_model=JobSeekerReferenceRead, status_code=status.HTTP_201_CREATED)
def create_reference(
    payload: JobSeekerReferenceCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerReferenceRead:
    data = payload.model_dump(mode="json")
    data["visibility"] = normalize_visibility(data.get("visibility"), allow_public=False)
    profile = get_or_create_profile(db, current_user.id)
    reference = JobSeekerReference(profile_id=profile.id, **data)
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return reference_response(reference)


@router.patch("/references/{reference_id}", response_model=JobSeekerReferenceRead)
def update_reference(
    reference_id: int,
    payload: JobSeekerReferenceUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> JobSeekerReferenceRead:
    profile = get_or_create_profile(db, current_user.id)
    reference = db.scalar(
        select(JobSeekerReference)
        .where(JobSeekerReference.id == reference_id)
        .where(JobSeekerReference.profile_id == profile.id)
    )
    if reference is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference not found")
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        if key == "visibility":
            value = normalize_visibility(value, allow_public=False)
        setattr(reference, key, value)
    db.commit()
    db.refresh(reference)
    return reference_response(reference)


@router.delete("/references/{reference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reference(
    reference_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    profile = get_or_create_profile(db, current_user.id)
    reference = db.scalar(
        select(JobSeekerReference)
        .where(JobSeekerReference.id == reference_id)
        .where(JobSeekerReference.profile_id == profile.id)
    )
    if reference is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference not found")
    db.delete(reference)
    db.commit()
