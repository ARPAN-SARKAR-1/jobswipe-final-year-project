"""Add support tickets.

Revision ID: 202606150002
Revises: 202606150001
Create Date: 2026-06-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202606150002"
down_revision: Union[str, None] = "202606150001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def upgrade() -> None:
    if has_table("support_tickets"):
        return
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("ticket_code", sa.String(length=40), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, index=True),
        sa.Column("role_type", sa.String(length=40), nullable=False, index=True),
        sa.Column("category", sa.String(length=80), nullable=False, index=True),
        sa.Column("priority", sa.String(length=20), nullable=False, index=True),
        sa.Column("subject", sa.String(length=150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="OPEN", index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("assigned_admin_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False, server_default="CONTACT_PAGE"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    # Non-destructive deployment migration; keep support ticket data on downgrade.
    pass
