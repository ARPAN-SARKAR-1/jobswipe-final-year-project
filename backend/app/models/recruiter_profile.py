from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class RecruiterProfile(TimestampMixin, Base):
    __tablename__ = "recruiter_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    official_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recruiter_verification_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    recruiter = relationship("User", foreign_keys=[user_id], back_populates="recruiter_profile")
    company = relationship("Company", back_populates="recruiters")
    verified_by_admin = relationship("User", foreign_keys=[verified_by_admin_id])
