"""Add company trust architecture.

Revision ID: 202606130001
Revises: 202606120001
Create Date: 2026-06-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202606130001"
down_revision: Union[str, None] = "202606120001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def has_column(table_name: str, column_name: str) -> bool:
    if not has_table(table_name):
        return False
    return column_name in {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def has_fk(table_name: str, fk_name: str) -> bool:
    if not has_table(table_name):
        return False
    return fk_name in {fk["name"] for fk in sa.inspect(op.get_bind()).get_foreign_keys(table_name)}


def has_index(table_name: str, index_name: str) -> bool:
    if not has_table(table_name):
        return False
    return index_name in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    if has_table("company_profiles"):
        if not has_column("company_profiles", "industry"):
            op.add_column("company_profiles", sa.Column("industry", sa.String(length=120), nullable=True))
        if not has_column("company_profiles", "company_type"):
            op.add_column(
                "company_profiles",
                sa.Column("company_type", sa.String(length=30), nullable=False, server_default="OTHER"),
            )
        if not has_column("company_profiles", "official_email_domain"):
            op.add_column("company_profiles", sa.Column("official_email_domain", sa.String(length=160), nullable=True))
        if not has_column("company_profiles", "verification_status"):
            op.add_column(
                "company_profiles",
                sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="PENDING"),
            )
            op.execute(
                """
                UPDATE company_profiles
                SET verification_status = CASE
                    WHEN recruiter_verification_status IN ('VERIFIED', 'REJECTED', 'SUSPENDED')
                    THEN recruiter_verification_status
                    ELSE 'PENDING'
                END
                """
            )

    if has_table("jobs"):
        if not has_column("jobs", "company_id"):
            op.add_column("jobs", sa.Column("company_id", sa.Integer(), nullable=True))
            if not has_index("jobs", "ix_jobs_company_id"):
                op.create_index("ix_jobs_company_id", "jobs", ["company_id"], unique=False)
            if not has_fk("jobs", "fk_jobs_company_id_company_profiles"):
                op.create_foreign_key(
                    "fk_jobs_company_id_company_profiles",
                    "jobs",
                    "company_profiles",
                    ["company_id"],
                    ["id"],
                    ondelete="SET NULL",
                )
            op.execute(
                """
                UPDATE jobs
                JOIN company_profiles ON company_profiles.recruiter_id = jobs.recruiter_id
                SET jobs.company_id = company_profiles.id
                WHERE jobs.company_id IS NULL
                """
            )
        if not has_column("jobs", "risk_score"):
            op.add_column("jobs", sa.Column("risk_score", sa.Integer(), nullable=False, server_default=sa.text("0")))
        if not has_column("jobs", "risk_flags"):
            op.add_column("jobs", sa.Column("risk_flags", sa.Text(), nullable=True))

    if not has_table("recruiter_company_members"):
        op.create_table(
            "recruiter_company_members",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("recruiter_id", sa.Integer(), nullable=False),
            sa.Column("company_id", sa.Integer(), nullable=False),
            sa.Column("designation", sa.String(length=120), nullable=True),
            sa.Column("work_email", sa.String(length=255), nullable=True),
            sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="PENDING"),
            sa.Column("company_join_status", sa.String(length=30), nullable=False, server_default="PENDING"),
            sa.Column("verified_at", sa.DateTime(), nullable=True),
            sa.Column("verified_by_admin_id", sa.Integer(), nullable=True),
            sa.Column("verified_by_company_owner_id", sa.Integer(), nullable=True),
            sa.Column("admin_note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["company_id"], ["company_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["verified_by_admin_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["verified_by_company_owner_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("recruiter_id", name="uq_recruiter_company_members_recruiter_id"),
            sa.UniqueConstraint("company_id", "recruiter_id", name="uq_recruiter_company_members_company_recruiter"),
        )
        op.create_index(op.f("ix_recruiter_company_members_id"), "recruiter_company_members", ["id"], unique=False)
        op.create_index(op.f("ix_recruiter_company_members_recruiter_id"), "recruiter_company_members", ["recruiter_id"], unique=False)
        op.create_index(op.f("ix_recruiter_company_members_company_id"), "recruiter_company_members", ["company_id"], unique=False)
        op.execute(
            """
            INSERT INTO recruiter_company_members (
                recruiter_id,
                company_id,
                verification_status,
                company_join_status,
                verified_at,
                verified_by_admin_id,
                admin_note,
                created_at,
                updated_at
            )
            SELECT
                recruiter_id,
                id,
                recruiter_verification_status,
                CASE WHEN recruiter_verification_status = 'VERIFIED' THEN 'APPROVED' ELSE 'PENDING' END,
                verified_at,
                verified_by_admin_id,
                verification_note,
                created_at,
                updated_at
            FROM company_profiles
            WHERE recruiter_id IS NOT NULL
            """
        )

    if not has_table("company_reviews"):
        op.create_table(
            "company_reviews",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("company_id", sa.Integer(), nullable=False),
            sa.Column("reviewer_user_id", sa.Integer(), nullable=False),
            sa.Column("application_id", sa.Integer(), nullable=True),
            sa.Column("rating", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("review_text", sa.Text(), nullable=False),
            sa.Column("work_culture_rating", sa.Integer(), nullable=True),
            sa.Column("interview_process_rating", sa.Integer(), nullable=True),
            sa.Column("growth_rating", sa.Integer(), nullable=True),
            sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("moderation_status", sa.String(length=30), nullable=False, server_default="VISIBLE"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_company_reviews_rating_range"),
            sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["company_id"], ["company_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "reviewer_user_id", name="uq_company_reviews_company_reviewer"),
        )
        op.create_index(op.f("ix_company_reviews_id"), "company_reviews", ["id"], unique=False)
        op.create_index(op.f("ix_company_reviews_company_id"), "company_reviews", ["company_id"], unique=False)
        op.create_index(op.f("ix_company_reviews_reviewer_user_id"), "company_reviews", ["reviewer_user_id"], unique=False)


def downgrade() -> None:
    pass
