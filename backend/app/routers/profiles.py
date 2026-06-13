from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_current_user
from app.models.company_profile import CompanyProfile
from app.models.enums import CompanyJoinStatus, JobSeekerVerificationStatus, ProfileVisibility, RecruiterVerificationStatus, UserRole
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.recruiter_company_member import RecruiterCompanyMember
from app.models.user import User
from app.models.user_document import UserDocument
from app.schemas.public_profile import (
    DocumentVisibilityUpdate,
    ProfileSettingsUpdate,
    PublicCompanySummary,
    PublicDocumentSummary,
    PublicProfileRead,
    UserDocumentRead,
    UsernameUpdate,
)
from app.services.public_identity import ensure_user_public_identity
from app.utils.file_upload import save_verification_document
from app.utils.public_identity import normalize_username
from app.utils.skills import split_skills

router = APIRouter(prefix="/profiles", tags=["Profiles"])

JOB_SEEKER_DOCUMENT_TYPES = {
    "resume",
    "marksheet_10",
    "marksheet_12",
    "diploma",
    "graduation",
    "post_graduation",
    "certificate",
}
RECRUITER_DOCUMENT_TYPES = {
    "government_id",
    "company_authorization",
    "hr_proof",
    "work_email_proof",
    "company_id_card",
    "certificate",
}
PRIVATE_ONLY_DOCUMENT_TYPES = {
    "resume",
    "marksheet_10",
    "marksheet_12",
    "diploma",
    "graduation",
    "post_graduation",
    "government_id",
    "company_authorization",
    "hr_proof",
    "work_email_proof",
    "company_id_card",
}


def can_view_private_profile(viewer: User | None, owner: User) -> bool:
    return bool(viewer and (viewer.id == owner.id or viewer.role in {UserRole.ADMIN.value, UserRole.OWNER.value}))


def document_response(document: UserDocument, include_file_url: bool = False) -> UserDocumentRead:
    return UserDocumentRead(
        id=document.id,
        owner_user_id=document.owner_user_id,
        document_type=document.document_type,
        original_filename=document.original_filename,
        is_public=document.is_public,
        verification_status=document.verification_status,
        reviewed_by=document.reviewed_by,
        reviewed_at=document.reviewed_at,
        review_note=document.review_note,
        file_url=document.file_url if include_file_url else None,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def document_summary(document: UserDocument) -> PublicDocumentSummary:
    return PublicDocumentSummary(
        id=document.id,
        document_type=document.document_type,
        title=document.original_filename or document.document_type.replace("_", " ").title(),
        verification_status=document.verification_status,
        created_at=document.created_at,
    )


def latest_recruiter_membership(db: Session, user_id: int) -> RecruiterCompanyMember | None:
    return db.scalar(
        select(RecruiterCompanyMember)
        .options(joinedload(RecruiterCompanyMember.company))
        .where(RecruiterCompanyMember.recruiter_id == user_id)
        .order_by(RecruiterCompanyMember.updated_at.desc())
        .limit(1)
    )


def company_summary(company: CompanyProfile | None, membership: RecruiterCompanyMember | None) -> PublicCompanySummary | None:
    if company is None:
        return None
    return PublicCompanySummary(
        id=company.id,
        public_company_id=company.public_company_id,
        slug=company.slug,
        name=company.company_name,
        logo_url=company.company_logo_url,
        designation=membership.designation if membership else None,
        verification_status=company.verification_status,
        recruiter_verification_status=membership.verification_status if membership else company.recruiter_verification_status,
        recruiter_verified=bool(membership and membership.verification_status == RecruiterVerificationStatus.VERIFIED.value),
        company_verified=company.verification_status == "VERIFIED",
    )


def public_profile_response(db: Session, user: User, viewer: User | None) -> PublicProfileRead:
    changed = ensure_user_public_identity(db, user)
    include_private = can_view_private_profile(viewer, user)
    visibility = user.profile_visibility or ProfileVisibility.PUBLIC.value
    is_limited = visibility == ProfileVisibility.PRIVATE.value and not include_private
    job_seeker_profile = user.job_seeker_profile
    membership = latest_recruiter_membership(db, user.id) if user.role == UserRole.RECRUITER.value else None
    company = (membership.company if membership else None) or user.company_profile

    verified_profile = False
    verification_label = None
    if user.role == UserRole.JOB_SEEKER.value and job_seeker_profile:
        verified_profile = job_seeker_profile.verification_status == JobSeekerVerificationStatus.VERIFIED.value
        verification_label = "Verified profile" if verified_profile else None
    if user.role == UserRole.RECRUITER.value and membership:
        verified_profile = membership.verification_status == RecruiterVerificationStatus.VERIFIED.value
        verification_label = "Verified recruiter" if verified_profile else None

    documents = list(
        db.scalars(
            select(UserDocument)
            .where(UserDocument.owner_user_id == user.id)
            .order_by(UserDocument.created_at.desc(), UserDocument.id.desc())
        ).all()
    )
    public_documents = [document_summary(document) for document in documents if document.is_public]
    private_documents = [document_response(document, include_file_url=True) for document in documents] if include_private else []

    if changed:
        db.flush()

    if is_limited:
        return PublicProfileRead(
            public_user_id=user.public_user_id,
            username=user.username,
            name=user.name,
            role=user.role,
            profile_picture_url=user.profile_picture_url,
            profile_visibility=visibility,
            is_limited=True,
            verified_profile=verified_profile,
            verification_label=verification_label,
            created_at=user.created_at,
        )

    return PublicProfileRead(
        public_user_id=user.public_user_id,
        username=user.username,
        name=user.name,
        role=user.role,
        profile_picture_url=user.profile_picture_url,
        profile_visibility=visibility,
        verified_profile=verified_profile,
        verification_label=verification_label,
        bio=user.bio or (job_seeker_profile.about if job_seeker_profile else None),
        skills=job_seeker_profile.skills if job_seeker_profile else None,
        skills_list=split_skills(job_seeker_profile.skills if job_seeker_profile else None),
        education=job_seeker_profile.education if job_seeker_profile else None,
        degree=job_seeker_profile.degree if job_seeker_profile else None,
        college=job_seeker_profile.college if job_seeker_profile else None,
        experience_level=job_seeker_profile.experience_level if job_seeker_profile else None,
        preferred_location=job_seeker_profile.preferred_location if job_seeker_profile else None,
        preferred_job_type=job_seeker_profile.preferred_job_type if job_seeker_profile else None,
        github_url=job_seeker_profile.github_url if job_seeker_profile else None,
        job_seeker_verification_status=job_seeker_profile.verification_status if job_seeker_profile else None,
        company=company_summary(company, membership),
        public_documents=public_documents,
        private_documents=private_documents,
        created_at=user.created_at,
    )


def get_user_by_username(db: Session, username: str) -> User:
    user = db.scalar(select(User).where(User.username == username.lower()))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return user


@router.get("/me", response_model=PublicProfileRead)
def get_my_public_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PublicProfileRead:
    profile = public_profile_response(db, current_user, current_user)
    db.commit()
    return profile


@router.get("/u/{username}", response_model=PublicProfileRead)
def get_public_profile_by_username(
    username: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> PublicProfileRead:
    profile = public_profile_response(db, get_user_by_username(db, username), current_user)
    db.commit()
    return profile


@router.get("/id/{public_user_id}", response_model=PublicProfileRead)
def get_public_profile_by_id(
    public_user_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> PublicProfileRead:
    user = db.scalar(select(User).where(User.public_user_id == public_user_id.upper()))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    profile = public_profile_response(db, user, current_user)
    db.commit()
    return profile


@router.put("/me/username", response_model=PublicProfileRead)
def update_username(
    payload: UsernameUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PublicProfileRead:
    username = normalize_username(payload.username)
    existing = db.scalar(select(User).where(User.username == username).where(User.id != current_user.id))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already taken")
    ensure_user_public_identity(db, current_user)
    current_user.username = username
    db.commit()
    db.refresh(current_user)
    return public_profile_response(db, current_user, current_user)


@router.put("/me/settings", response_model=PublicProfileRead)
def update_profile_settings(
    payload: ProfileSettingsUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PublicProfileRead:
    ensure_user_public_identity(db, current_user)
    current_user.bio = payload.bio
    current_user.profile_visibility = payload.profile_visibility.value
    if current_user.role == UserRole.JOB_SEEKER.value:
        profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == current_user.id))
        if profile and payload.bio is not None:
            profile.about = payload.bio
    db.commit()
    db.refresh(current_user)
    return public_profile_response(db, current_user, current_user)


@router.get("/me/documents", response_model=list[UserDocumentRead])
def list_my_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserDocumentRead]:
    documents = db.scalars(
        select(UserDocument).where(UserDocument.owner_user_id == current_user.id).order_by(UserDocument.created_at.desc())
    ).all()
    return [document_response(document, include_file_url=True) for document in documents]


@router.post("/me/documents", response_model=UserDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_my_document(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    document_type: Annotated[str, Form(..., min_length=3, max_length=60)],
    file: UploadFile = File(...),
    is_public: Annotated[bool, Form()] = False,
) -> UserDocumentRead:
    normalized_type = document_type.strip().lower()
    if current_user.role == UserRole.JOB_SEEKER.value:
        allowed_types = JOB_SEEKER_DOCUMENT_TYPES
    elif current_user.role == UserRole.RECRUITER.value:
        allowed_types = RECRUITER_DOCUMENT_TYPES
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only job seekers and recruiters can upload profile documents.")
    if normalized_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported document type for this account.")
    public_flag = bool(is_public and normalized_type not in PRIVATE_ONLY_DOCUMENT_TYPES)
    url = await save_verification_document(file)
    document = UserDocument(
        owner_user_id=current_user.id,
        document_type=normalized_type,
        file_url=url,
        original_filename=file.filename,
        is_public=public_flag,
    )
    db.add(document)
    if normalized_type == "resume" and current_user.role == UserRole.JOB_SEEKER.value:
        profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == current_user.id))
        if profile:
            profile.resume_pdf_url = url
    db.commit()
    db.refresh(document)
    return document_response(document, include_file_url=True)


@router.put("/me/documents/{document_id}/visibility", response_model=UserDocumentRead)
def update_document_visibility(
    document_id: int,
    payload: DocumentVisibilityUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserDocumentRead:
    document = db.scalar(select(UserDocument).where(UserDocument.id == document_id).where(UserDocument.owner_user_id == current_user.id))
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if payload.is_public and document.document_type in PRIVATE_ONLY_DOCUMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This document type must remain private.")
    document.is_public = payload.is_public
    db.commit()
    db.refresh(document)
    return document_response(document, include_file_url=True)
