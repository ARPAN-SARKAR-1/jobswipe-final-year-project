"""Add company and recruiter review analytics.

Revision ID: 202605240003
Revises: 202605240002
Create Date: 2026-05-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202605240003"
down_revision: Union[str, None] = "202605240002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("company_reviews", sa.Column("application_id", sa.Integer(), nullable=True))
    op.add_column("company_reviews", sa.Column("overall_rating", sa.Integer(), nullable=False, server_default="5"))
    op.add_column("company_reviews", sa.Column("work_culture_rating", sa.Integer(), nullable=False, server_default="5"))
    op.add_column("company_reviews", sa.Column("interview_process_rating", sa.Integer(), nullable=False, server_default="5"))
    op.add_column("company_reviews", sa.Column("salary_transparency_rating", sa.Integer(), nullable=False, server_default="5"))
    op.add_column("company_reviews", sa.Column("growth_opportunity_rating", sa.Integer(), nullable=False, server_default="5"))
    op.add_column("company_reviews", sa.Column("review_title", sa.String(length=160), nullable=True))
    op.add_column("company_reviews", sa.Column("pros", sa.Text(), nullable=True))
    op.add_column("company_reviews", sa.Column("cons", sa.Text(), nullable=True))
    op.add_column("company_reviews", sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("company_reviews", sa.Column("moderation_status", sa.String(length=30), nullable=False, server_default="VISIBLE"))
    op.create_foreign_key(
        "fk_company_reviews_application_id_applications",
        "company_reviews",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        """
        UPDATE company_reviews
        SET overall_rating = rating,
            work_culture_rating = rating,
            interview_process_rating = rating,
            salary_transparency_rating = rating,
            growth_opportunity_rating = rating,
            moderation_status = CASE WHEN is_visible = 1 THEN 'VISIBLE' ELSE 'HIDDEN' END
        """
    )

    op.add_column("recruiter_profiles", sa.Column("average_rating", sa.Float(), nullable=False, server_default="0"))
    op.add_column("recruiter_profiles", sa.Column("total_reviews", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "recruiter_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recruiter_id", sa.Integer(), nullable=False),
        sa.Column("job_seeker_id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=True),
        sa.Column("overall_rating", sa.Integer(), nullable=False),
        sa.Column("communication_rating", sa.Integer(), nullable=False),
        sa.Column("response_time_rating", sa.Integer(), nullable=False),
        sa.Column("professionalism_rating", sa.Integer(), nullable=False),
        sa.Column("transparency_rating", sa.Integer(), nullable=False),
        sa.Column("review_title", sa.String(length=160), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("moderation_status", sa.String(length=30), nullable=False, server_default="VISIBLE"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("overall_rating >= 1 AND overall_rating <= 5", name="ck_recruiter_reviews_overall_rating_range"),
        sa.CheckConstraint("communication_rating >= 1 AND communication_rating <= 5", name="ck_recruiter_reviews_communication_rating_range"),
        sa.CheckConstraint("response_time_rating >= 1 AND response_time_rating <= 5", name="ck_recruiter_reviews_response_time_rating_range"),
        sa.CheckConstraint("professionalism_rating >= 1 AND professionalism_rating <= 5", name="ck_recruiter_reviews_professionalism_rating_range"),
        sa.CheckConstraint("transparency_rating >= 1 AND transparency_rating <= 5", name="ck_recruiter_reviews_transparency_rating_range"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recruiter_id", "job_seeker_id", name="uq_recruiter_review_recruiter_job_seeker"),
    )
    op.create_index(op.f("ix_recruiter_reviews_id"), "recruiter_reviews", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recruiter_reviews_id"), table_name="recruiter_reviews")
    op.drop_table("recruiter_reviews")
    op.drop_column("recruiter_profiles", "total_reviews")
    op.drop_column("recruiter_profiles", "average_rating")
    op.drop_constraint("fk_company_reviews_application_id_applications", "company_reviews", type_="foreignkey")
    op.drop_column("company_reviews", "moderation_status")
    op.drop_column("company_reviews", "is_anonymous")
    op.drop_column("company_reviews", "cons")
    op.drop_column("company_reviews", "pros")
    op.drop_column("company_reviews", "review_title")
    op.drop_column("company_reviews", "growth_opportunity_rating")
    op.drop_column("company_reviews", "salary_transparency_rating")
    op.drop_column("company_reviews", "interview_process_rating")
    op.drop_column("company_reviews", "work_culture_rating")
    op.drop_column("company_reviews", "overall_rating")
    op.drop_column("company_reviews", "application_id")
