"""Add optional accessibility profile fields.

Revision ID: 202606200001
Revises: 202606180001
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202606200001"
down_revision: Union[str, None] = "202606180001"
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
    add_column_if_missing(
        "job_seeker_profiles",
        sa.Column("has_accessibility_needs", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    add_column_if_missing("job_seeker_profiles", sa.Column("accessibility_needs", sa.Text(), nullable=True))
    add_column_if_missing("job_seeker_profiles", sa.Column("accessibility_notes", sa.Text(), nullable=True))
    add_column_if_missing(
        "job_seeker_profiles",
        sa.Column("accessibility_visibility", sa.String(length=30), nullable=False, server_default="PRIVATE"),
    )


def downgrade() -> None:
    # Non-destructive deployment migration; keep candidate accommodation data on downgrade.
    pass
