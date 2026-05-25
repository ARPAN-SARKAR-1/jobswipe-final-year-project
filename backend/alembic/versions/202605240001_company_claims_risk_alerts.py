"""Add company claims, company members, and risk assessments.

Revision ID: 202605240001
Revises: 202605200001
Create Date: 2026-05-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202605240001"
down_revision: Union[str, None] = "202605200001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_role", sa.String(length=40), nullable=False, server_default="COMPANY_RECRUITER"),
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("requested_at", sa.DateTime(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("verified_by_user_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "user_id", name="uq_company_members_company_user"),
    )
    op.create_index(op.f("ix_company_members_id"), "company_members", ["id"], unique=False)

    op.create_table(
        "company_claim_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("requested_company_name", sa.String(length=160), nullable=False),
        sa.Column("requested_domain", sa.String(length=160), nullable=False),
        sa.Column("requester_user_id", sa.Integer(), nullable=False),
        sa.Column("official_email", sa.String(length=255), nullable=False),
        sa.Column("claim_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("verification_token_hash", sa.String(length=128), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("email_verified_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(length=30), nullable=False, server_default="LOW"),
        sa.Column("requires_admin_review", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("risk_reasons", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requester_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_company_claim_requests_id"), "company_claim_requests", ["id"], unique=False)

    op.create_table(
        "job_risk_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(length=30), nullable=False, server_default="LOW"),
        sa.Column("reasons", sa.Text(), nullable=True),
        sa.Column("auto_action", sa.String(length=30), nullable=False, server_default="NONE"),
        sa.Column("reviewed_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", name="uq_job_risk_assessments_job_id"),
    )
    op.create_index(op.f("ix_job_risk_assessments_id"), "job_risk_assessments", ["id"], unique=False)

    op.create_table(
        "candidate_risk_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_seeker_id", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(length=30), nullable=False, server_default="LOW"),
        sa.Column("reasons", sa.Text(), nullable=True),
        sa.Column("reviewed_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_seeker_id", name="uq_candidate_risk_assessments_job_seeker_id"),
    )
    op.create_index(op.f("ix_candidate_risk_assessments_id"), "candidate_risk_assessments", ["id"], unique=False)

    conn = op.get_bind()
    profiles = conn.execute(
        sa.text(
            """
            SELECT rp.id, rp.user_id, rp.company_id, rp.recruiter_verification_status,
                   rp.verified_at, rp.verified_by_admin_id, rp.created_at, rp.updated_at
            FROM recruiter_profiles rp
            WHERE rp.company_id IS NOT NULL
            ORDER BY rp.company_id ASC, rp.id ASC
            """
        )
    ).mappings().all()
    seen_companies: set[int] = set()
    for profile in profiles:
        company_id = int(profile["company_id"])
        company_role = "COMPANY_OWNER" if company_id not in seen_companies else "COMPANY_RECRUITER"
        seen_companies.add(company_id)
        conn.execute(
            sa.text(
                """
                INSERT INTO company_members (
                    company_id, user_id, company_role, verification_status, requested_at,
                    verified_at, verified_by_user_id, note, created_at, updated_at
                )
                VALUES (
                    :company_id, :user_id, :company_role, :verification_status, :requested_at,
                    :verified_at, :verified_by_user_id, :note, :created_at, :updated_at
                )
                """
            ),
            {
                "company_id": company_id,
                "user_id": profile["user_id"],
                "company_role": company_role,
                "verification_status": profile["recruiter_verification_status"] or "PENDING",
                "requested_at": profile["created_at"],
                "verified_at": profile["verified_at"],
                "verified_by_user_id": profile["verified_by_admin_id"],
                "note": "Backfilled from recruiter verification profile.",
                "created_at": profile["created_at"],
                "updated_at": profile["updated_at"],
            },
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_candidate_risk_assessments_id"), table_name="candidate_risk_assessments")
    op.drop_table("candidate_risk_assessments")
    op.drop_index(op.f("ix_job_risk_assessments_id"), table_name="job_risk_assessments")
    op.drop_table("job_risk_assessments")
    op.drop_index(op.f("ix_company_claim_requests_id"), table_name="company_claim_requests")
    op.drop_table("company_claim_requests")
    op.drop_index(op.f("ix_company_members_id"), table_name="company_members")
    op.drop_table("company_members")
