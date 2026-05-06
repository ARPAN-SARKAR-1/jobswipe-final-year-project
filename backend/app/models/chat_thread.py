from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ChatThread(TimestampMixin, Base):
    __tablename__ = "chat_threads"
    __table_args__ = (UniqueConstraint("application_id", name="uq_chat_thread_application"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_seeker_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    started_by_recruiter: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    application = relationship("Application", back_populates="chat_thread")
    recruiter = relationship("User", foreign_keys=[recruiter_id], back_populates="recruiter_chat_threads")
    job_seeker = relationship("User", foreign_keys=[job_seeker_id], back_populates="job_seeker_chat_threads")
    job = relationship("Job", back_populates="chat_threads")
    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan")

    @property
    def job_title(self) -> str | None:
        return self.job.title if self.job else None

    @property
    def company_name(self) -> str | None:
        return self.job.company_name if self.job else None

    @property
    def recruiter_name(self) -> str | None:
        return self.recruiter.name if self.recruiter else None

    @property
    def job_seeker_name(self) -> str | None:
        return self.job_seeker.name if self.job_seeker else None

    @property
    def application_status(self) -> str | None:
        return self.application.status if self.application else None
