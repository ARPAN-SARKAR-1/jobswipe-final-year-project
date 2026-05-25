from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class RecruiterReview(TimestampMixin, Base):
    __tablename__ = "recruiter_reviews"
    __table_args__ = (
        UniqueConstraint("recruiter_id", "job_seeker_id", name="uq_recruiter_review_recruiter_job_seeker"),
        CheckConstraint("overall_rating >= 1 AND overall_rating <= 5", name="ck_recruiter_reviews_overall_rating_range"),
        CheckConstraint("communication_rating >= 1 AND communication_rating <= 5", name="ck_recruiter_reviews_communication_rating_range"),
        CheckConstraint("response_time_rating >= 1 AND response_time_rating <= 5", name="ck_recruiter_reviews_response_time_rating_range"),
        CheckConstraint("professionalism_rating >= 1 AND professionalism_rating <= 5", name="ck_recruiter_reviews_professionalism_rating_range"),
        CheckConstraint("transparency_rating >= 1 AND transparency_rating <= 5", name="ck_recruiter_reviews_transparency_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_seeker_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    communication_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    professionalism_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    transparency_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    moderation_status: Mapped[str] = mapped_column(String(30), default="VISIBLE", nullable=False)

    recruiter = relationship("User", foreign_keys=[recruiter_id], back_populates="recruiter_reviews_received")
    job_seeker = relationship("User", foreign_keys=[job_seeker_id], back_populates="recruiter_reviews_given")
    application = relationship("Application")
