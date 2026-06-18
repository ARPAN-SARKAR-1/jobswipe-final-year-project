from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import (
    CompanyJoinStatus,
    CompanyType,
    CompanyVerificationStatus,
    ExperienceVerificationStatus,
    GraduationVerificationStatus,
    JobSeekerCategory,
    RecruiterVerificationStatus,
    SectionVisibility,
    StudentVerificationStatus,
)
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
    job_seeker_category: JobSeekerCategory | None = None
    college_name: str | None = Field(default=None, max_length=180)
    university_name: str | None = Field(default=None, max_length=180)
    course_name: str | None = Field(default=None, max_length=160)
    degree_name: str | None = Field(default=None, max_length=160)
    department_or_branch: str | None = Field(default=None, max_length=160)
    current_year_or_semester: str | None = Field(default=None, max_length=80)
    expected_passing_year: int | None = Field(default=None, ge=1950, le=2100)
    college_location: str | None = Field(default=None, max_length=160)
    student_id_number: str | None = Field(default=None, max_length=120)
    internship_interest: bool = False
    preferred_internship_roles: str | None = None
    highest_degree: str | None = Field(default=None, max_length=160)
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    specialization_or_branch: str | None = Field(default=None, max_length=160)
    fresher_skills: str | None = None
    certifications: str | None = None
    project_links: str | None = None
    internship_experience: str | None = None
    preferred_job_roles: str | None = None
    total_experience_years: float | None = Field(default=None, ge=0, le=80)
    current_or_last_company: str | None = Field(default=None, max_length=180)
    current_or_last_role: str | None = Field(default=None, max_length=160)
    employment_type: str | None = Field(default=None, max_length=80)
    notice_period: str | None = Field(default=None, max_length=80)
    previous_companies: str | None = None
    role_history: str | None = None
    key_responsibilities: str | None = None
    tools_technologies: str | None = None
    achievements: str | None = None
    preferred_next_roles: str | None = None
    education_visibility: SectionVisibility = SectionVisibility.PUBLIC
    experience_visibility: SectionVisibility = SectionVisibility.PUBLIC
    recommendation_visibility: SectionVisibility = SectionVisibility.PRIVATE
    reference_visibility: SectionVisibility = SectionVisibility.PRIVATE
    certificate_visibility: SectionVisibility = SectionVisibility.PUBLIC

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
    student_verification_status: str = "STUDENT_UNVERIFIED"
    graduation_verification_status: str = "GRADUATION_UNVERIFIED"
    experience_verification_status: str = "EXPERIENCE_UNVERIFIED"
    certificates_public: bool = False
    profile_completion_percentage: int = 0
    missing_profile_fields: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileUpdate(BaseModel):
    company_name: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    company_size: str | None = Field(default=None, max_length=30)
    employee_count_estimate: int | None = Field(default=None, ge=0)
    headquarters: str | None = Field(default=None, max_length=160)
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    company_type: CompanyType | None = None
    description: str | None = None
    location: str | None = Field(default=None, max_length=160)
    career_page_url: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    glassdoor_url: str | None = Field(default=None, max_length=500)
    ambitionbox_url: str | None = Field(default=None, max_length=500)
    about_company: str | None = None
    culture_summary: str | None = None
    benefits: str | None = None
    hiring_process: str | None = None
    work_mode: str | None = Field(default=None, max_length=40)
    rating_source: str | None = Field(default=None, max_length=40)
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
    company_completion_percentage: int = 0
    missing_company_fields: list[str] = []
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


class JobSeekerCategoryUpdate(BaseModel):
    job_seeker_category: JobSeekerCategory


class JobSeekerRecommendationBase(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    organization: str | None = Field(default=None, max_length=180)
    issued_by: str | None = Field(default=None, max_length=160)
    issue_date: date | None = None
    file_url: str | None = Field(default=None, max_length=500)
    visibility: SectionVisibility = SectionVisibility.PRIVATE


class JobSeekerRecommendationCreate(JobSeekerRecommendationBase):
    pass


class JobSeekerRecommendationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    organization: str | None = Field(default=None, max_length=180)
    issued_by: str | None = Field(default=None, max_length=160)
    issue_date: date | None = None
    file_url: str | None = Field(default=None, max_length=500)
    visibility: SectionVisibility | None = None


class JobSeekerRecommendationRead(JobSeekerRecommendationBase):
    id: int
    verification_status: str = "PENDING"
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobSeekerReferenceBase(BaseModel):
    reference_name: str = Field(min_length=2, max_length=160)
    reference_role: str | None = Field(default=None, max_length=160)
    organization: str | None = Field(default=None, max_length=180)
    relationship: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    visibility: SectionVisibility = SectionVisibility.PRIVATE
    note: str | None = Field(default=None, max_length=1000)


class JobSeekerReferenceCreate(JobSeekerReferenceBase):
    pass


class JobSeekerReferenceUpdate(BaseModel):
    reference_name: str | None = Field(default=None, min_length=2, max_length=160)
    reference_role: str | None = Field(default=None, max_length=160)
    organization: str | None = Field(default=None, max_length=180)
    relationship: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    visibility: SectionVisibility | None = None
    note: str | None = Field(default=None, max_length=1000)


class JobSeekerReferenceRead(JobSeekerReferenceBase):
    id: int
    verification_status: str = "PENDING"
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
