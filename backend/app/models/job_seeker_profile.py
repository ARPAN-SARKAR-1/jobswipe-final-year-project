from sqlalchemy import ForeignKey, Integer, String, Text
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

    user = relationship("User", back_populates="job_seeker_profile")
