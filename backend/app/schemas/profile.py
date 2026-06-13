from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import CompanyJoinStatus, CompanyType, CompanyVerificationStatus, RecruiterVerificationStatus
from app.utils.skills import normalize_skills, split_skills


class JobSeekerProfileUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=30)
    github_url: str | None = Field(default=None, max_length=255)
    about: str | None = Field(default=None, max_length=2000)
    education: str | None = Field(default=None, max_length=160)
    degree: str | None = Field(default=None, max_length=160)
    college: str | None = Field(default=None, max_length=180)
    passing_year: int | None = Field(default=None, ge=1950, le=2100)
    cgpa_or_percentage: str | None = Field(default=None, max_length=40)
    skills: str | None = None
    experience_level: str | None = Field(default=None, max_length=40)
    preferred_location: str | None = Field(default=None, max_length=160)
    preferred_job_type: str | None = Field(default=None, max_length=40)

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
    public_user_id: str | None = None
    username: str | None = None
    name: str
    email: str
    profile_picture_url: str | None = None
    resume_pdf_url: str | None = None
    verification_status: str = "PENDING"
    certificates_public: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileUpdate(BaseModel):
    company_name: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    company_type: CompanyType | None = None
    description: str | None = None
    location: str | None = Field(default=None, max_length=160)
    official_email_domain: str | None = Field(default=None, max_length=160)
    designation: str | None = Field(default=None, max_length=120)
    work_email: str | None = Field(default=None, max_length=255)


class CompanyJoinRequest(BaseModel):
    company_id: int
    designation: str | None = Field(default=None, max_length=120)
    work_email: str | None = Field(default=None, max_length=255)


class CompanyProfileRead(CompanyProfileUpdate):
    id: int
    public_company_id: str | None = None
    slug: str | None = None
    recruiter_id: int
    name: str | None = None
    company_logo_url: str | None = None
    logo_url: str | None = None
    verification_status: CompanyVerificationStatus = CompanyVerificationStatus.PENDING
    recruiter_verification_status: RecruiterVerificationStatus = RecruiterVerificationStatus.PENDING
    company_join_status: CompanyJoinStatus = CompanyJoinStatus.PENDING
    designation: str | None = None
    work_email: str | None = None
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
    membership_id: int | None = None
    member_verification_status: RecruiterVerificationStatus = RecruiterVerificationStatus.PENDING
    member_join_status: CompanyJoinStatus = CompanyJoinStatus.PENDING
    member_admin_note: str | None = None


class UploadResponse(BaseModel):
    url: str
    message: str
