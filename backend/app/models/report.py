from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    recruiter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    report_type: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_made")
    recruiter = relationship("User", foreign_keys=[recruiter_id], back_populates="recruiter_reports")
    job = relationship("Job", back_populates="reports")

    @property
    def reporter_name(self) -> str | None:
        return self.reporter.name if self.reporter else None

    @property
    def reporter_email(self) -> str | None:
        return self.reporter.email if self.reporter else None

    @property
    def recruiter_name(self) -> str | None:
        return self.recruiter.name if self.recruiter else None

    @property
    def recruiter_email(self) -> str | None:
        return self.recruiter.email if self.recruiter else None

    @property
    def job_title(self) -> str | None:
        return self.job.title if self.job else None
