from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    profile_picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accepted_terms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accepted_terms_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    accepted_privacy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accepted_privacy_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    account_status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    suspension_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_protected_owner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    job_seeker_profile = relationship("JobSeekerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    company_profile = relationship(
        "CompanyProfile",
        foreign_keys="CompanyProfile.recruiter_id",
        back_populates="recruiter",
        uselist=False,
        cascade="all, delete-orphan",
    )
    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job_seeker", cascade="all, delete-orphan")
    swipes = relationship("Swipe", back_populates="job_seeker", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    recruiter_chat_threads = relationship(
        "ChatThread",
        foreign_keys="ChatThread.recruiter_id",
        back_populates="recruiter",
    )
    job_seeker_chat_threads = relationship(
        "ChatThread",
        foreign_keys="ChatThread.job_seeker_id",
        back_populates="job_seeker",
    )
    chat_messages = relationship("ChatMessage", foreign_keys="ChatMessage.sender_id", back_populates="sender")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    reports_made = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
    recruiter_reports = relationship("Report", foreign_keys="Report.recruiter_id", back_populates="recruiter")
