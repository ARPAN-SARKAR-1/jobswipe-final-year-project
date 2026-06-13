from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class JobSeekerReference(TimestampMixin, Base):
    __tablename__ = "job_seeker_references"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_seeker_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    reference_name: Mapped[str] = mapped_column(String(160), nullable=False)
    reference_role: Mapped[str | None] = mapped_column(String(160), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(180), nullable=True)
    relationship: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), default="PRIVATE", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile = orm_relationship("JobSeekerProfile", back_populates="references")
