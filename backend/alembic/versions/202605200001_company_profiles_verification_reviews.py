"""Add company profiles, recruiter profiles, and company reviews.

Revision ID: 202605200001
Revises: 202605060003
Create Date: 2026-05-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202605200001"
down_revision: Union[str, None] = "202605060003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=160), nullable=False),
        sa.Column("company_logo_url", sa.String(length=500), nullable=True),
        sa.Column("company_type", sa.String(length=80), nullable=False, server_default="Other"),
        sa.Column("industry", sa.String(length=160), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("official_email_domain", sa.String(length=160), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("headquarters_location", sa.String(length=160), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("company_size", sa.String(length=80), nullable=True),
        sa.Column("registration_number", sa.String(length=120), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.Column("verified_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("average_rating", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_reviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["verified_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_id"), "companies", ["id"], unique=False)

    op.create_table(
        "recruiter_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("designation", sa.String(length=120), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("official_email", sa.String(length=255), nullable=True),
        sa.Column("recruiter_verification_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.Column("verified_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_recruiter_profiles_user_id"),
    )
    op.create_index(op.f("ix_recruiter_profiles_id"), "recruiter_profiles", ["id"], unique=False)

    op.add_column("jobs", sa.Column("company_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_jobs_company_id_companies",
        "jobs",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "company_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("job_seeker_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_company_reviews_rating_range"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "job_seeker_id", name="uq_company_review_company_job_seeker"),
    )
    op.create_index(op.f("ix_company_reviews_id"), "company_reviews", ["id"], unique=False)

    conn = op.get_bind()
    legacy_profiles = conn.execute(
        sa.text(
            """
            SELECT id, recruiter_id, company_name, company_logo_url, website, description, location,
                   recruiter_verification_status, verification_note, verified_at, verified_by_admin_id,
                   created_at, updated_at
            FROM company_profiles
            """
        )
    ).mappings().all()

    for legacy in legacy_profiles:
        status_value = legacy["recruiter_verification_status"] or "PENDING"
        company_name = legacy["company_name"] or f"Company {legacy['recruiter_id']}"
        result = conn.execute(
            sa.text(
                """
                INSERT INTO companies (
                    company_name, company_logo_url, company_type, website, description,
                    headquarters_location, verification_status, verification_note,
                    verified_at, verified_by_admin_id, created_at, updated_at
                )
                VALUES (
                    :company_name, :company_logo_url, 'Other', :website, :description,
                    :headquarters_location, :verification_status, :verification_note,
                    :verified_at, :verified_by_admin_id, :created_at, :updated_at
                )
                """
            ),
            {
                "company_name": company_name,
                "company_logo_url": legacy["company_logo_url"],
                "website": legacy["website"],
                "description": legacy["description"],
                "headquarters_location": legacy["location"],
                "verification_status": status_value,
                "verification_note": legacy["verification_note"],
                "verified_at": legacy["verified_at"],
                "verified_by_admin_id": legacy["verified_by_admin_id"],
                "created_at": legacy["created_at"],
                "updated_at": legacy["updated_at"],
            },
        )
        company_id = result.lastrowid
        conn.execute(
            sa.text(
                """
                INSERT INTO recruiter_profiles (
                    user_id, company_id, official_email, recruiter_verification_status,
                    verification_note, verified_at, verified_by_admin_id, created_at, updated_at
                )
                SELECT u.id, :company_id, u.email, :status_value, :verification_note,
                       :verified_at, :verified_by_admin_id, :created_at, :updated_at
                FROM users u
                WHERE u.id = :recruiter_id
                """
            ),
            {
                "company_id": company_id,
                "status_value": status_value,
                "verification_note": legacy["verification_note"],
                "verified_at": legacy["verified_at"],
                "verified_by_admin_id": legacy["verified_by_admin_id"],
                "created_at": legacy["created_at"],
                "updated_at": legacy["updated_at"],
                "recruiter_id": legacy["recruiter_id"],
            },
        )
        conn.execute(
            sa.text("UPDATE jobs SET company_id = :company_id WHERE recruiter_id = :recruiter_id AND company_id IS NULL"),
            {"company_id": company_id, "recruiter_id": legacy["recruiter_id"]},
        )

    recruiters_without_profiles = conn.execute(
        sa.text(
            """
            SELECT id, name, email, created_at, updated_at
            FROM users
            WHERE role = 'RECRUITER'
              AND id NOT IN (SELECT user_id FROM recruiter_profiles)
            """
        )
    ).mappings().all()
    for recruiter in recruiters_without_profiles:
        result = conn.execute(
            sa.text(
                """
                INSERT INTO companies (company_name, company_type, verification_status, created_at, updated_at)
                VALUES (:company_name, 'Other', 'PENDING', :created_at, :updated_at)
                """
            ),
            {
                "company_name": f"{recruiter['name']}'s Company",
                "created_at": recruiter["created_at"],
                "updated_at": recruiter["updated_at"],
            },
        )
        company_id = result.lastrowid
        conn.execute(
            sa.text(
                """
                INSERT INTO recruiter_profiles (user_id, company_id, official_email, recruiter_verification_status, created_at, updated_at)
                VALUES (:user_id, :company_id, :official_email, 'PENDING', :created_at, :updated_at)
                """
            ),
            {
                "user_id": recruiter["id"],
                "company_id": company_id,
                "official_email": recruiter["email"],
                "created_at": recruiter["created_at"],
                "updated_at": recruiter["updated_at"],
            },
        )
        conn.execute(
            sa.text("UPDATE jobs SET company_id = :company_id WHERE recruiter_id = :recruiter_id AND company_id IS NULL"),
            {"company_id": company_id, "recruiter_id": recruiter["id"]},
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_company_reviews_id"), table_name="company_reviews")
    op.drop_table("company_reviews")

    op.drop_constraint("fk_jobs_company_id_companies", "jobs", type_="foreignkey")
    op.drop_column("jobs", "company_id")

    op.drop_index(op.f("ix_recruiter_profiles_id"), table_name="recruiter_profiles")
    op.drop_table("recruiter_profiles")

    op.drop_index(op.f("ix_companies_id"), table_name="companies")
    op.drop_table("companies")
