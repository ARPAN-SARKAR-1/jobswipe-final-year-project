"""Add final platform upgrade tables and fields.

Revision ID: 202605060003
Revises: 202605060002
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202605060003"
down_revision: Union[str, None] = "202605060002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("accepted_privacy", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.add_column("users", sa.Column("accepted_privacy_at", sa.DateTime(), nullable=True))

    op.add_column(
        "company_profiles",
        sa.Column("recruiter_verification_status", sa.String(length=30), nullable=False, server_default="PENDING"),
    )
    op.add_column("company_profiles", sa.Column("verification_note", sa.Text(), nullable=True))
    op.add_column("company_profiles", sa.Column("verified_at", sa.DateTime(), nullable=True))
    op.add_column("company_profiles", sa.Column("verified_by_admin_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_company_profiles_verified_by_admin_id_users",
        "company_profiles",
        "users",
        ["verified_by_admin_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=80), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("link_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_id"), "notifications", ["id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("recruiter_id", sa.Integer(), nullable=True),
        sa.Column("report_type", sa.String(length=60), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_id"), "reports", ["id"], unique=False)

    op.create_table(
        "application_timelines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("old_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_application_timelines_id"), "application_timelines", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_application_timelines_id"), table_name="application_timelines")
    op.drop_table("application_timelines")

    op.drop_index(op.f("ix_reports_id"), table_name="reports")
    op.drop_table("reports")

    op.drop_index(op.f("ix_notifications_id"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_constraint("fk_company_profiles_verified_by_admin_id_users", "company_profiles", type_="foreignkey")
    op.drop_column("company_profiles", "verified_by_admin_id")
    op.drop_column("company_profiles", "verified_at")
    op.drop_column("company_profiles", "verification_note")
    op.drop_column("company_profiles", "recruiter_verification_status")

    op.drop_column("users", "accepted_privacy_at")
    op.drop_column("users", "accepted_privacy")
