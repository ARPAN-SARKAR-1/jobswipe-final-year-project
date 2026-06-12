"""Add OTP, CAPTCHA, 2FA, and trusted-device security tables.

Revision ID: 202606120001
Revises: 202605060003
Create Date: 2026-06-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202606120001"
down_revision: Union[str, None] = "202605060003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("1")))
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("twofa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")))

    op.create_table(
        "email_otps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("otp_hash", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_otps_id"), "email_otps", ["id"], unique=False)
    op.create_index(op.f("ix_email_otps_user_id"), "email_otps", ["user_id"], unique=False)

    op.create_table(
        "captcha_challenges",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("answer_hash", sa.String(length=128), nullable=False),
        sa.Column("question", sa.String(length=120), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_captcha_challenges_purpose"), "captcha_challenges", ["purpose"], unique=False)

    op.create_table(
        "login_otp_challenges",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("otp_hash", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_otp_challenges_user_id"), "login_otp_challenges", ["user_id"], unique=False)

    op.create_table(
        "trusted_devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trusted_devices_id"), "trusted_devices", ["id"], unique=False)
    op.create_index(op.f("ix_trusted_devices_token_hash"), "trusted_devices", ["token_hash"], unique=True)
    op.create_index(op.f("ix_trusted_devices_user_id"), "trusted_devices", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trusted_devices_user_id"), table_name="trusted_devices")
    op.drop_index(op.f("ix_trusted_devices_token_hash"), table_name="trusted_devices")
    op.drop_index(op.f("ix_trusted_devices_id"), table_name="trusted_devices")
    op.drop_table("trusted_devices")

    op.drop_index(op.f("ix_login_otp_challenges_user_id"), table_name="login_otp_challenges")
    op.drop_table("login_otp_challenges")

    op.drop_index(op.f("ix_captcha_challenges_purpose"), table_name="captcha_challenges")
    op.drop_table("captcha_challenges")

    op.drop_index(op.f("ix_email_otps_user_id"), table_name="email_otps")
    op.drop_index(op.f("ix_email_otps_id"), table_name="email_otps")
    op.drop_table("email_otps")

    op.drop_column("users", "twofa_enabled")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "email_verified")
