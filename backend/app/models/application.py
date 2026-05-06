from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Application(TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_seeker_id", "job_id", name="uq_application_job_seeker_job"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_seeker_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    admin_status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    job_seeker = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    chat_thread = relationship("ChatThread", back_populates="application", uselist=False, cascade="all, delete-orphan")
    timeline_events = relationship("ApplicationTimeline", back_populates="application", cascade="all, delete-orphan")

    @property
    def chat_thread_id(self) -> int | None:
        return self.chat_thread.id if self.chat_thread else None

    @property
    def chat_status(self) -> str | None:
        return self.chat_thread.status if self.chat_thread else None
