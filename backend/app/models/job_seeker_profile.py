from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class JobSeekerProfile(TimestampMixin, Base):
    __tablename__ = "job_seeker_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    education: Mapped[str | None] = mapped_column(String(160), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(160), nullable=True)
    college: Mapped[str | None] = mapped_column(String(180), nullable=True)
    passing_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cgpa_or_percentage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    preferred_location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    preferred_job_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    academic_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    degree_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    stream_or_branch: Mapped[str | None] = mapped_column(String(160), nullable=True)
    college_or_university: Mapped[str | None] = mapped_column(String(180), nullable=True)
    admission_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_year: Mapped[str | None] = mapped_column(String(40), nullable=True)
    current_semester: Mapped[str | None] = mapped_column(String(40), nullable=True)
    current_cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    internship_preference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    preferred_internship_duration: Mapped[str | None] = mapped_column(String(80), nullable=True)
    available_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    open_to_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    open_to_relocation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    final_cgpa_or_percentage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    looking_for: Mapped[str | None] = mapped_column(String(80), nullable=True)

    user = relationship("User", back_populates="job_seeker_profile")
