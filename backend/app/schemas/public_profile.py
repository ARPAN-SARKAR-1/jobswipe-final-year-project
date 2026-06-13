from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentVerificationStatus, ProfileVisibility, SectionVisibility, UserRole


class UsernameUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=30)


class ProfileSettingsUpdate(BaseModel):
    bio: str | None = Field(default=None, max_length=2000)
    profile_visibility: ProfileVisibility = ProfileVisibility.PUBLIC


class DocumentVisibilityUpdate(BaseModel):
    is_public: bool = False
    visibility: SectionVisibility | None = None


class DocumentReviewRequest(BaseModel):
    verification_status: DocumentVerificationStatus
    review_note: str | None = Field(default=None, max_length=1000)


class UserDocumentRead(BaseModel):
    id: int
    owner_user_id: int
    document_type: str
    original_filename: str | None = None
    is_public: bool
    visibility: SectionVisibility = SectionVisibility.PRIVATE
    verification_status: DocumentVerificationStatus = DocumentVerificationStatus.PENDING
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    file_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicDocumentSummary(BaseModel):
    id: int
    document_type: str
    title: str
    verification_status: DocumentVerificationStatus = DocumentVerificationStatus.PENDING
    created_at: datetime


class PublicCompanySummary(BaseModel):
    id: int
    public_company_id: str | None = None
    slug: str | None = None
    name: str | None = None
    logo_url: str | None = None
    designation: str | None = None
    verification_status: str | None = None
    recruiter_verification_status: str | None = None
    recruiter_verified: bool = False
    company_verified: bool = False


class PublicProfileRead(BaseModel):
    public_user_id: str
    username: str | None = None
    name: str
    role: UserRole
    profile_picture_url: str | None = None
    profile_visibility: ProfileVisibility = ProfileVisibility.PUBLIC
    is_limited: bool = False
    verified_profile: bool = False
    verification_label: str | None = None
    bio: str | None = None
    skills: str | None = None
    skills_list: list[str] = []
    education: str | None = None
    degree: str | None = None
    college: str | None = None
    experience_level: str | None = None
    preferred_location: str | None = None
    preferred_job_type: str | None = None
    github_url: str | None = None
    job_seeker_verification_status: str | None = None
    job_seeker_category: str | None = None
    college_name: str | None = None
    university_name: str | None = None
    course_name: str | None = None
    degree_name: str | None = None
    department_or_branch: str | None = None
    current_year_or_semester: str | None = None
    expected_passing_year: int | None = None
    college_location: str | None = None
    internship_interest: bool | None = None
    preferred_internship_roles: str | None = None
    highest_degree: str | None = None
    graduation_year: int | None = None
    specialization_or_branch: str | None = None
    fresher_skills: str | None = None
    certifications: str | None = None
    project_links: str | None = None
    internship_experience: str | None = None
    preferred_job_roles: str | None = None
    total_experience_years: float | None = None
    current_or_last_company: str | None = None
    current_or_last_role: str | None = None
    employment_type: str | None = None
    notice_period: str | None = None
    previous_companies: str | None = None
    role_history: str | None = None
    key_responsibilities: str | None = None
    tools_technologies: str | None = None
    achievements: str | None = None
    preferred_next_roles: str | None = None
    student_verification_status: str | None = None
    graduation_verification_status: str | None = None
    experience_verification_status: str | None = None
    company: PublicCompanySummary | None = None
    public_documents: list[PublicDocumentSummary] = []
    private_documents: list[UserDocumentRead] = []
    created_at: datetime


class AdminUserDocumentRead(UserDocumentRead):
    owner_name: str | None = None
    owner_email: str | None = None
    owner_role: str | None = None
