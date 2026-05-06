from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import RecruiterVerificationStatus
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


class CompanyProfileUpdate(BaseModel):
    company_name: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=255)
    description: str | None = None
    location: str | None = Field(default=None, max_length=160)


class CompanyProfileRead(CompanyProfileUpdate):
    id: int
    recruiter_id: int
    company_logo_url: str | None = None
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
