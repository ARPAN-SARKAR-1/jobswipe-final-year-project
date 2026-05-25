"""Add job seeker academic profiles and protected documents.

Revision ID: 202605250001
Revises: 202605240003
Create Date: 2026-05-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202605250001"
down_revision: Union[str, None] = "202605240003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("job_seeker_profiles", sa.Column("academic_status", sa.String(length=30), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("degree_name", sa.String(length=160), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("stream_or_branch", sa.String(length=160), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("college_or_university", sa.String(length=180), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("admission_year", sa.Integer(), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("expected_graduation_year", sa.Integer(), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("current_year", sa.String(length=40), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("current_semester", sa.String(length=40), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("current_cgpa", sa.Float(), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("internship_preference", sa.String(length=80), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("preferred_internship_duration", sa.String(length=80), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("available_from", sa.Date(), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("open_to_remote", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("job_seeker_profiles", sa.Column("open_to_relocation", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("job_seeker_profiles", sa.Column("final_cgpa_or_percentage", sa.String(length=40), nullable=True))
    op.add_column("job_seeker_profiles", sa.Column("looking_for", sa.String(length=80), nullable=True))

    op.add_column("jobs", sa.Column("eligible_academic_status", sa.String(length=30), nullable=False, server_default="BOTH"))
    op.add_column("jobs", sa.Column("eligible_streams", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("minimum_cgpa", sa.Float(), nullable=True))
    op.add_column("jobs", sa.Column("eligible_graduation_years", sa.String(length=255), nullable=True))
    op.add_column("jobs", sa.Column("internship_available", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "job_seeker_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_seeker_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("related_skill", sa.String(length=120), nullable=True),
        sa.Column("issuing_organization", sa.String(length=180), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("credential_url", sa.String(length=500), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index(op.f("ix_job_seeker_documents_id"), "job_seeker_documents", ["id"], unique=False)
    op.create_index(op.f("ix_job_seeker_documents_job_seeker_id"), "job_seeker_documents", ["job_seeker_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_seeker_documents_job_seeker_id"), table_name="job_seeker_documents")
    op.drop_index(op.f("ix_job_seeker_documents_id"), table_name="job_seeker_documents")
    op.drop_table("job_seeker_documents")

    op.drop_column("jobs", "internship_available")
    op.drop_column("jobs", "eligible_graduation_years")
    op.drop_column("jobs", "minimum_cgpa")
    op.drop_column("jobs", "eligible_streams")
    op.drop_column("jobs", "eligible_academic_status")

    op.drop_column("job_seeker_profiles", "looking_for")
    op.drop_column("job_seeker_profiles", "final_cgpa_or_percentage")
    op.drop_column("job_seeker_profiles", "open_to_relocation")
    op.drop_column("job_seeker_profiles", "open_to_remote")
    op.drop_column("job_seeker_profiles", "available_from")
    op.drop_column("job_seeker_profiles", "preferred_internship_duration")
    op.drop_column("job_seeker_profiles", "internship_preference")
    op.drop_column("job_seeker_profiles", "current_cgpa")
    op.drop_column("job_seeker_profiles", "current_semester")
    op.drop_column("job_seeker_profiles", "current_year")
    op.drop_column("job_seeker_profiles", "expected_graduation_year")
    op.drop_column("job_seeker_profiles", "admission_year")
    op.drop_column("job_seeker_profiles", "college_or_university")
    op.drop_column("job_seeker_profiles", "stream_or_branch")
    op.drop_column("job_seeker_profiles", "degree_name")
    op.drop_column("job_seeker_profiles", "academic_status")
