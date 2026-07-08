"""Add job screening questions.

Revision ID: 202607080001
Revises: 202606200001
Create Date: 2026-07-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202607080001"
down_revision: Union[str, None] = "202606200001"
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
    add_column_if_missing("jobs", sa.Column("screening_questions", sa.Text(), nullable=True))
    add_column_if_missing("applications", sa.Column("screening_answers", sa.Text(), nullable=True))


def downgrade() -> None:
    # Keep application screening history on downgrade; this migration is non-destructive.
    pass
