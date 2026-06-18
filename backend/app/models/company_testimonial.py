from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CompanyTestimonialStatus, CompanyTestimonialVisibility
from app.models.mixins import TimestampMixin


class CompanyTestimonial(TimestampMixin, Base):
    __tablename__ = "company_testimonials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), default=CompanyTestimonialVisibility.PUBLIC.value, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=CompanyTestimonialStatus.PENDING_ADMIN_REVIEW.value, nullable=False)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    company = relationship("CompanyProfile", back_populates="testimonials")
    creator = relationship("User", foreign_keys=[created_by_user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
