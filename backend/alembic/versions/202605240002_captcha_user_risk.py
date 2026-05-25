"""Add captcha, security settings, login attempts, and user risk.

Revision ID: 202605240002
Revises: 202605240001
Create Date: 2026-05-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202605240002"
down_revision: Union[str, None] = "202605240001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "captcha_challenges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("challenge_id", sa.String(length=64), nullable=False),
        sa.Column("answer_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_captcha_challenges_id"), "captcha_challenges", ["id"], unique=False)
    op.create_index(op.f("ix_captcha_challenges_challenge_id"), "captcha_challenges", ["challenge_id"], unique=True)

    op.create_table(
        "security_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("captcha_login_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("captcha_signup_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("captcha_forgot_password_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("captcha_reports_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("captcha_company_claims_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_security_settings_id"), "security_settings", ["id"], unique=False)
    op.execute(
        """
        INSERT INTO security_settings
            (id, captcha_login_enabled, captcha_signup_enabled, captcha_forgot_password_enabled, captcha_reports_enabled, captcha_company_claims_enabled)
        VALUES
            (1, 1, 1, 1, 0, 0)
        """
    )

    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role_selected", sa.String(length=30), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("failure_reason", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_attempts_id"), "login_attempts", ["id"], unique=False)
    op.create_index(op.f("ix_login_attempts_email"), "login_attempts", ["email"], unique=False)

    op.create_table(
        "user_risk_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(length=30), nullable=False, server_default="LOW"),
        sa.Column("reasons", sa.Text(), nullable=True),
        sa.Column("last_evaluated_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["reviewed_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_risk_assessments_user_id"),
    )
    op.create_index(op.f("ix_user_risk_assessments_id"), "user_risk_assessments", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_risk_assessments_id"), table_name="user_risk_assessments")
    op.drop_table("user_risk_assessments")
    op.drop_index(op.f("ix_login_attempts_email"), table_name="login_attempts")
    op.drop_index(op.f("ix_login_attempts_id"), table_name="login_attempts")
    op.drop_table("login_attempts")
    op.drop_index(op.f("ix_security_settings_id"), table_name="security_settings")
    op.drop_table("security_settings")
    op.drop_index(op.f("ix_captcha_challenges_challenge_id"), table_name="captcha_challenges")
    op.drop_index(op.f("ix_captcha_challenges_id"), table_name="captcha_challenges")
    op.drop_table("captcha_challenges")
