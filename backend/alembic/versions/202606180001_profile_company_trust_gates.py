"""Add profile completion and company trust fields.

Revision ID: 202606180001
Revises: 202606150002
Create Date: 2026-06-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202606180001"
down_revision: Union[str, None] = "202606150002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def has_column(table_name: str, column_name: str) -> bool:
    if not has_table(table_name):
        return False
    columns = sa.inspect(op.get_bind()).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if has_table(table_name) and not has_column(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    add_column_if_missing("company_profiles", sa.Column("company_size", sa.String(length=30), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("employee_count_estimate", sa.Integer(), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("headquarters", sa.String(length=160), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("founded_year", sa.Integer(), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("career_page_url", sa.String(length=500), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("linkedin_url", sa.String(length=500), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("glassdoor_url", sa.String(length=500), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("ambitionbox_url", sa.String(length=500), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("about_company", sa.Text(), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("culture_summary", sa.Text(), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("benefits", sa.Text(), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("hiring_process", sa.Text(), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("work_mode", sa.String(length=40), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("rating_source", sa.String(length=40), nullable=True))

    add_column_if_missing("jobs", sa.Column("career_page_url", sa.String(length=500), nullable=True))
    add_column_if_missing("jobs", sa.Column("official_apply_url", sa.String(length=500), nullable=True))
    add_column_if_missing(
        "jobs",
        sa.Column("source_type", sa.String(length=40), nullable=False, server_default="COMPANY_PORTAL"),
    )
    add_column_if_missing(
        "jobs",
        sa.Column("career_link_status", sa.String(length=40), nullable=False, server_default="LINK_NOT_CHECKED"),
    )
    add_column_if_missing("jobs", sa.Column("career_link_warning", sa.Text(), nullable=True))

    if not has_table("company_testimonials"):
        op.create_table(
            "company_testimonials",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("title", sa.String(length=180), nullable=False),
            sa.Column("statement", sa.Text(), nullable=False),
            sa.Column("reviewer_label", sa.String(length=160), nullable=True),
            sa.Column("rating", sa.Integer(), nullable=True),
            sa.Column("visibility", sa.String(length=30), nullable=False, server_default="PUBLIC", index=True),
            sa.Column("status", sa.String(length=40), nullable=False, server_default="PENDING_ADMIN_REVIEW", index=True),
            sa.Column("admin_note", sa.Text(), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )


def downgrade() -> None:
    # Non-destructive deployment migration; keep added trust/profile data on downgrade.
    pass
