"""Add bond and admin moderation controls.

Revision ID: 202605020001
Revises: 202605010001
Create Date: 2026-05-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202605020001"
down_revision: Union[str, None] = "202605010001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("account_status", sa.String(length=30), nullable=False, server_default="ACTIVE"))
    op.add_column("users", sa.Column("suspension_reason", sa.Text(), nullable=True))

    op.add_column("jobs", sa.Column("has_bond", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.add_column("jobs", sa.Column("bond_years", sa.Float(), nullable=True))
    op.add_column("jobs", sa.Column("bond_details", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("moderation_status", sa.String(length=30), nullable=False, server_default="ACTIVE"))
    op.add_column("jobs", sa.Column("moderation_reason", sa.Text(), nullable=True))

    op.add_column("applications", sa.Column("admin_status", sa.String(length=30), nullable=False, server_default="ACTIVE"))
    op.add_column("applications", sa.Column("admin_note", sa.Text(), nullable=True))

    op.create_table(
        "admin_action_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=60), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_action_logs_id"), "admin_action_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_action_logs_id"), table_name="admin_action_logs")
    op.drop_table("admin_action_logs")

    op.drop_column("applications", "admin_note")
    op.drop_column("applications", "admin_status")

    op.drop_column("jobs", "moderation_reason")
    op.drop_column("jobs", "moderation_status")
    op.drop_column("jobs", "bond_details")
    op.drop_column("jobs", "bond_years")
    op.drop_column("jobs", "has_bond")

    op.drop_column("users", "suspension_reason")
    op.drop_column("users", "account_status")
