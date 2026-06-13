"""Add job seeker categories, recommendations, and references.

Revision ID: 202606150001
Revises: 202606140001
Create Date: 2026-06-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202606150001"
down_revision: Union[str, None] = "202606140001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def has_column(table_name: str, column_name: str) -> bool:
    if not has_table(table_name):
        return False
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}
    return column_name in columns


def add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not has_column(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    if has_table("job_seeker_profiles"):
        add_column_if_missing("job_seeker_profiles", sa.Column("job_seeker_category", sa.String(length=40), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("college_name", sa.String(length=180), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("university_name", sa.String(length=180), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("course_name", sa.String(length=160), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("degree_name", sa.String(length=160), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("department_or_branch", sa.String(length=160), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("current_year_or_semester", sa.String(length=80), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("expected_passing_year", sa.Integer(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("college_location", sa.String(length=160), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("student_id_number", sa.String(length=120), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("internship_interest", sa.Boolean(), server_default=sa.false(), nullable=False))
        add_column_if_missing("job_seeker_profiles", sa.Column("preferred_internship_roles", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("highest_degree", sa.String(length=160), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("graduation_year", sa.Integer(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("specialization_or_branch", sa.String(length=160), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("fresher_skills", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("certifications", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("project_links", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("internship_experience", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("preferred_job_roles", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("total_experience_years", sa.Float(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("current_or_last_company", sa.String(length=180), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("current_or_last_role", sa.String(length=160), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("employment_type", sa.String(length=80), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("notice_period", sa.String(length=80), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("previous_companies", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("role_history", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("key_responsibilities", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("tools_technologies", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("achievements", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("preferred_next_roles", sa.Text(), nullable=True))
        add_column_if_missing("job_seeker_profiles", sa.Column("education_visibility", sa.String(length=30), server_default="PUBLIC", nullable=False))
        add_column_if_missing("job_seeker_profiles", sa.Column("experience_visibility", sa.String(length=30), server_default="PUBLIC", nullable=False))
        add_column_if_missing("job_seeker_profiles", sa.Column("recommendation_visibility", sa.String(length=30), server_default="PRIVATE", nullable=False))
        add_column_if_missing("job_seeker_profiles", sa.Column("reference_visibility", sa.String(length=30), server_default="PRIVATE", nullable=False))
        add_column_if_missing("job_seeker_profiles", sa.Column("certificate_visibility", sa.String(length=30), server_default="PUBLIC", nullable=False))
        add_column_if_missing("job_seeker_profiles", sa.Column("student_verification_status", sa.String(length=40), server_default="STUDENT_UNVERIFIED", nullable=False))
        add_column_if_missing("job_seeker_profiles", sa.Column("graduation_verification_status", sa.String(length=40), server_default="GRADUATION_UNVERIFIED", nullable=False))
        add_column_if_missing("job_seeker_profiles", sa.Column("experience_verification_status", sa.String(length=40), server_default="EXPERIENCE_UNVERIFIED", nullable=False))

    if has_table("user_documents") and not has_column("user_documents", "visibility"):
        op.add_column("user_documents", sa.Column("visibility", sa.String(length=30), server_default="PRIVATE", nullable=False))
        op.execute("UPDATE user_documents SET visibility = CASE WHEN is_public = 1 THEN 'PUBLIC' ELSE 'PRIVATE' END")

    if not has_table("job_seeker_recommendations"):
        op.create_table(
            "job_seeker_recommendations",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("profile_id", sa.Integer(), sa.ForeignKey("job_seeker_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("title", sa.String(length=180), nullable=False),
            sa.Column("organization", sa.String(length=180), nullable=True),
            sa.Column("issued_by", sa.String(length=160), nullable=True),
            sa.Column("issue_date", sa.Date(), nullable=True),
            sa.Column("file_url", sa.String(length=500), nullable=True),
            sa.Column("visibility", sa.String(length=30), server_default="PRIVATE", nullable=False),
            sa.Column("verification_status", sa.String(length=30), server_default="PENDING", nullable=False),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("review_note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    if not has_table("job_seeker_references"):
        op.create_table(
            "job_seeker_references",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("profile_id", sa.Integer(), sa.ForeignKey("job_seeker_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("reference_name", sa.String(length=160), nullable=False),
            sa.Column("reference_role", sa.String(length=160), nullable=True),
            sa.Column("organization", sa.String(length=180), nullable=True),
            sa.Column("relationship", sa.String(length=120), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("phone", sa.String(length=40), nullable=True),
            sa.Column("visibility", sa.String(length=30), server_default="PRIVATE", nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("verification_status", sa.String(length=30), server_default="PENDING", nullable=False),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("review_note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )


def downgrade() -> None:
    # Non-destructive deployment migration; keep data on downgrade.
    pass
