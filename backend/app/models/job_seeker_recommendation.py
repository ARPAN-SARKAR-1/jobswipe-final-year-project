from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class JobSeekerRecommendation(TimestampMixin, Base):
    __tablename__ = "job_seeker_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_seeker_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(180), nullable=True)
    issued_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), default="PRIVATE", nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile = relationship("JobSeekerProfile", back_populates="recommendations")
