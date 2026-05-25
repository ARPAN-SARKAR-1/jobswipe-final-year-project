from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import (
    AcademicStatus,
    CompanyType,
    CompanyVerificationStatus,
    CurrentAcademicYear,
    EligibleAcademicStatus,
    GraduateLookingFor,
    InternshipPreference,
    JobSeekerDocumentType,
    RecruiterVerificationStatus,
)
from app.utils.skills import normalize_skills, split_skills


class JobSeekerProfileUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=30)
    github_url: str | None = Field(default=None, max_length=255)
    education: str | None = Field(default=None, max_length=160)
    degree: str | None = Field(default=None, max_length=160)
    college: str | None = Field(default=None, max_length=180)
    passing_year: int | None = Field(default=None, ge=1950, le=2100)
    cgpa_or_percentage: str | None = Field(default=None, max_length=40)
    skills: str | None = None
    experience_level: str | None = Field(default=None, max_length=40)
    preferred_location: str | None = Field(default=None, max_length=160)
    preferred_job_type: str | None = Field(default=None, max_length=40)
    academic_status: AcademicStatus | None = None
    degree_name: str | None = Field(default=None, max_length=160)
    stream_or_branch: str | None = Field(default=None, max_length=160)
    college_or_university: str | None = Field(default=None, max_length=180)
    admission_year: int | None = Field(default=None, ge=1950, le=2100)
    expected_graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    current_year: CurrentAcademicYear | None = None
    current_semester: str | None = Field(default=None, max_length=40)
    current_cgpa: float | None = Field(default=None, ge=0, le=10)
    internship_preference: InternshipPreference | None = None
    preferred_internship_duration: str | None = Field(default=None, max_length=80)
    available_from: date | None = None
    open_to_remote: bool = False
    open_to_relocation: bool = False
    final_cgpa_or_percentage: str | None = Field(default=None, max_length=40)
    looking_for: GraduateLookingFor | None = None

    @field_validator("skills", mode="before")
    @classmethod
    def normalize_profile_skills(cls, value: Any) -> str | None:
        if value is None:
            return None
        return normalize_skills(value)

    @computed_field
    @property
    def skills_list(self) -> list[str]:
        return split_skills(self.skills)


class JobSeekerProfileRead(JobSeekerProfileUpdate):
    id: int
    user_id: int
    name: str
    email: str
    profile_picture_url: str | None = None
    resume_pdf_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobSeekerDocumentRead(BaseModel):
    id: int
    job_seeker_id: int
    document_type: JobSeekerDocumentType
    title: str
    file_url: str
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    is_verified: bool = False
    related_skill: str | None = None
    issuing_organization: str | None = None
    issue_date: date | None = None
    credential_url: str | None = None
    uploaded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecruiterApplicantDocumentRead(BaseModel):
    id: int
    document_type: JobSeekerDocumentType
    title: str
    file_url: str
    mime_type: str
    file_size: int
    related_skill: str | None = None
    issuing_organization: str | None = None
    issue_date: date | None = None
    credential_url: str | None = None
    is_verified: bool = False

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileUpdate(BaseModel):
    company_name: str | None = Field(default=None, max_length=160)
    company_type: CompanyType | None = None
    industry: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=255)
    official_email_domain: str | None = Field(default=None, max_length=160)
    description: str | None = None
    headquarters_location: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    company_size: str | None = Field(default=None, max_length=80)
    registration_number: str | None = Field(default=None, max_length=120)
    company_id: int | None = None
    designation: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    official_email: str | None = Field(default=None, max_length=255)

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            raise ValueError("Company name is required")
        return text

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        candidate = text if "://" in text else f"https://{text}"
        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Website must be a valid URL")
        return candidate

    @field_validator("official_email_domain")
    @classmethod
    def normalize_official_email_domain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        domain = value.strip().lower().lstrip("@")
        if not domain:
            return None
        if any(char.isspace() for char in domain) or "/" in domain or "@" in domain or "." not in domain:
            raise ValueError("Official email domain must be a valid domain")
        return domain


class CompanyProfileRead(CompanyProfileUpdate):
    id: int
    recruiter_id: int
    company_id: int | None = None
    company_logo_url: str | None = None
    verification_status: CompanyVerificationStatus = CompanyVerificationStatus.PENDING
    company_verification_note: str | None = None
    company_verified_at: datetime | None = None
    company_verified_by_admin_id: int | None = None
    average_rating: float = 0
    total_reviews: int = 0
    recruiter_verification_status: RecruiterVerificationStatus = RecruiterVerificationStatus.PENDING
    verification_note: str | None = None
    verified_at: datetime | None = None
    verified_by_admin_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminRecruiterVerificationRead(CompanyProfileRead):
    recruiter_name: str
    recruiter_email: str
    account_status: str


class UploadResponse(BaseModel):
    url: str
    message: str
