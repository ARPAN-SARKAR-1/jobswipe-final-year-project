from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApplicationAdminStatus, ApplicationStatus
from app.schemas.job import JobRead
from app.schemas.profile import RecruiterApplicantDocumentRead


class ApplicationCreate(BaseModel):
    job_id: int
    resume_pdf_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=255)


class ApplicationRead(BaseModel):
    id: int
    job_seeker_id: int
    job_id: int
    resume_pdf_url: str | None = None
    github_url: str | None = None
    status: ApplicationStatus
    admin_status: ApplicationAdminStatus = ApplicationAdminStatus.ACTIVE
    admin_note: str | None = None
    chat_thread_id: int | None = None
    chat_status: str | None = None
    created_at: datetime
    updated_at: datetime
    job: JobRead | None = None

    model_config = ConfigDict(from_attributes=True)


class RecruiterApplicationRead(ApplicationRead):
    applicant_name: str
    applicant_email: str
    applicant_github_url: str | None = None
    applicant_resume_pdf_url: str | None = None
    applicant_academic_status: str | None = None
    applicant_degree_name: str | None = None
    applicant_stream_or_branch: str | None = None
    applicant_college_or_university: str | None = None
    applicant_graduation_year: int | None = None
    applicant_current_year: str | None = None
    applicant_cgpa: float | None = None
    applicant_experience_level: str | None = None
    applicant_internship_preference: str | None = None
    applicant_open_to_remote: bool = False
    applicant_open_to_relocation: bool = False
    applicant_skills: str | None = None
    applicant_documents: list[RecruiterApplicantDocumentRead] = Field(default_factory=list)
    job_title: str


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class CandidateReportCreate(BaseModel):
    reason: str = Field(min_length=10, max_length=1000)


class ApplicationTimelineRead(BaseModel):
    id: int
    application_id: int
    action: str
    old_status: str | None = None
    new_status: str | None = None
    note: str | None = None
    created_by_user_id: int | None = None
    created_by_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
