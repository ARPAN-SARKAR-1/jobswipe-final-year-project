from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CompanyType, CompanyVerificationStatus, RecruiterVerificationStatus
from app.schemas.job import JobRead


class CompanyRead(BaseModel):
    id: int
    company_name: str
    company_logo_url: str | None = None
    company_type: CompanyType = CompanyType.OTHER
    industry: str | None = None
    website: str | None = None
    official_email_domain: str | None = None
    description: str | None = None
    headquarters_location: str | None = None
    founded_year: int | None = None
    company_size: str | None = None
    registration_number: str | None = None
    verification_status: CompanyVerificationStatus = CompanyVerificationStatus.PENDING
    verification_note: str | None = None
    verified_by_admin_id: int | None = None
    verified_at: datetime | None = None
    average_rating: float = 0
    total_reviews: int = 0
    active_jobs_count: int = 0
    recruiter_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyRecruiterRead(BaseModel):
    id: int
    user_id: int
    recruiter_name: str
    recruiter_email: str
    designation: str | None = None
    department: str | None = None
    official_email: str | None = None
    recruiter_verification_status: RecruiterVerificationStatus = RecruiterVerificationStatus.PENDING
    account_status: str
    verified_at: datetime | None = None


class CompanyDetailRead(CompanyRead):
    recruiters: list[CompanyRecruiterRead] = Field(default_factory=list)
    active_jobs: list[JobRead] = Field(default_factory=list)


class CompanyReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    review_text: str | None = Field(default=None, max_length=3000)


class CompanyReviewRead(BaseModel):
    id: int
    company_id: int
    job_seeker_id: int
    rating: int
    review_text: str | None = None
    is_visible: bool = True
    reviewer_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminCompanyReviewRead(CompanyReviewRead):
    company_name: str | None = None
    reviewer_email: str | None = None
