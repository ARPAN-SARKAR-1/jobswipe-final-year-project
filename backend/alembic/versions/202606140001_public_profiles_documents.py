"""Add public profiles and private verification documents.

Revision ID: 202606140001
Revises: 202606130001
Create Date: 2026-06-14
"""

from typing import Any, Sequence, Union
import re
import secrets
import string

from alembic import op
import sqlalchemy as sa

revision: str = "202606140001"
down_revision: Union[str, None] = "202606130001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ALPHABET = string.ascii_uppercase + string.digits
RESERVED_USERNAMES = {
    "admin",
    "owner",
    "login",
    "register",
    "api",
    "support",
    "security",
    "privacy",
    "company",
    "companies",
    "jobs",
    "recruiter",
    "jobseeker",
}


def inspector() -> Any:
    return sa.inspect(op.get_bind())


def has_table(table_name: str) -> bool:
    return inspector().has_table(table_name)


def has_column(table_name: str, column_name: str) -> bool:
    if not has_table(table_name):
        return False
    return column_name in {column["name"] for column in inspector().get_columns(table_name)}


def has_index(table_name: str, index_name: str) -> bool:
    if not has_table(table_name):
        return False
    return index_name in {index["name"] for index in inspector().get_indexes(table_name)}


def has_fk(table_name: str, fk_name: str) -> bool:
    if not has_table(table_name):
        return False
    return fk_name in {fk["name"] for fk in inspector().get_foreign_keys(table_name)}


def generate_public_id(prefix: str, used: set[str], length: int = 12) -> str:
    prefix = "".join(char for char in prefix.upper() if char in ALPHABET)[:4]
    for _ in range(100):
        token = "".join(secrets.choice(ALPHABET) for _ in range(max(length - len(prefix), 8)))
        candidate = f"{prefix}{token}"[:length]
        if candidate not in used:
            used.add(candidate)
            return candidate
    raise RuntimeError("Could not generate unique public identifier during migration.")


def username_seed(value: str | None, fallback: str) -> str:
    seed = re.sub(r"[^a-z0-9_-]+", "-", (value or fallback).lower()).strip("-_")
    if not seed:
        seed = fallback
    if len(seed) < 3:
        seed = f"{seed}user"
    seed = seed[:24].strip("-_") or fallback
    if seed in RESERVED_USERNAMES:
        seed = f"{seed}-user"
    return seed[:30]


def unique_username(seed: str, used: set[str]) -> str:
    base = username_seed(seed, "user")
    for index in range(1000):
        candidate = base if index == 0 else f"{base[: max(3, 29 - len(str(index)))]}-{index}"
        if candidate not in used and candidate not in RESERVED_USERNAMES and re.fullmatch(r"[a-z0-9_-]{3,30}", candidate):
            used.add(candidate)
            return candidate
    raise RuntimeError("Could not generate unique username during migration.")


def slug_seed(value: str | None, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or fallback).lower()).strip("-")
    return (slug[:80].strip("-") or fallback)


def unique_slug(seed: str | None, used: set[str]) -> str:
    base = slug_seed(seed, "company")
    for index in range(1000):
        candidate = base if index == 0 else f"{base[: max(3, 78 - len(str(index)))]}-{index}"
        if candidate not in used:
            used.add(candidate)
            return candidate
    raise RuntimeError("Could not generate unique company slug during migration.")


def add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if has_table(table_name) and not has_column(table_name, column.name):
        op.add_column(table_name, column)


def backfill_users() -> None:
    if not has_table("users"):
        return
    connection = op.get_bind()
    existing_ids = {
        row[0]
        for row in connection.execute(sa.text("SELECT public_user_id FROM users WHERE public_user_id IS NOT NULL AND public_user_id != ''"))
    }
    existing_usernames = {
        row[0]
        for row in connection.execute(sa.text("SELECT username FROM users WHERE username IS NOT NULL AND username != ''"))
    }
    rows = connection.execute(sa.text("SELECT id, email, name FROM users")).mappings().all()
    for row in rows:
        values: dict[str, str | int] = {"id": row["id"]}
        if not connection.execute(sa.text("SELECT public_user_id FROM users WHERE id=:id"), {"id": row["id"]}).scalar():
            values["public_user_id"] = generate_public_id("SFS", existing_ids)
        if not connection.execute(sa.text("SELECT username FROM users WHERE id=:id"), {"id": row["id"]}).scalar():
            seed = (row["email"] or "").split("@", 1)[0] or row["name"] or "user"
            values["username"] = unique_username(seed, existing_usernames)
        if len(values) > 1:
            set_clause = ", ".join(f"{key}=:{key}" for key in values if key != "id")
            connection.execute(sa.text(f"UPDATE users SET {set_clause} WHERE id=:id"), values)


def backfill_companies() -> None:
    if not has_table("company_profiles"):
        return
    connection = op.get_bind()
    existing_ids = {
        row[0]
        for row in connection.execute(
            sa.text("SELECT public_company_id FROM company_profiles WHERE public_company_id IS NOT NULL AND public_company_id != ''")
        )
    }
    existing_slugs = {
        row[0]
        for row in connection.execute(sa.text("SELECT slug FROM company_profiles WHERE slug IS NOT NULL AND slug != ''"))
    }
    rows = connection.execute(sa.text("SELECT id, company_name FROM company_profiles")).mappings().all()
    for row in rows:
        values: dict[str, str | int] = {"id": row["id"]}
        if not connection.execute(sa.text("SELECT public_company_id FROM company_profiles WHERE id=:id"), {"id": row["id"]}).scalar():
            values["public_company_id"] = generate_public_id("CMP", existing_ids)
        if not connection.execute(sa.text("SELECT slug FROM company_profiles WHERE id=:id"), {"id": row["id"]}).scalar():
            values["slug"] = unique_slug(row["company_name"], existing_slugs)
        if len(values) > 1:
            set_clause = ", ".join(f"{key}=:{key}" for key in values if key != "id")
            connection.execute(sa.text(f"UPDATE company_profiles SET {set_clause} WHERE id=:id"), values)


def backfill_jobs() -> None:
    if not has_table("jobs"):
        return
    connection = op.get_bind()
    existing_ids = {
        row[0]
        for row in connection.execute(sa.text("SELECT job_public_id FROM jobs WHERE job_public_id IS NOT NULL AND job_public_id != ''"))
    }
    rows = connection.execute(sa.text("SELECT id FROM jobs WHERE job_public_id IS NULL OR job_public_id = ''")).mappings().all()
    for row in rows:
        connection.execute(
            sa.text("UPDATE jobs SET job_public_id=:job_public_id WHERE id=:id"),
            {"id": row["id"], "job_public_id": generate_public_id("JOB", existing_ids)},
        )


def upgrade() -> None:
    add_column_if_missing("users", sa.Column("public_user_id", sa.String(length=12), nullable=True))
    add_column_if_missing("users", sa.Column("username", sa.String(length=30), nullable=True))
    add_column_if_missing("users", sa.Column("bio", sa.Text(), nullable=True))
    add_column_if_missing("users", sa.Column("profile_visibility", sa.String(length=20), nullable=False, server_default="PUBLIC"))
    backfill_users()
    if not has_index("users", "ux_users_public_user_id"):
        op.create_index("ux_users_public_user_id", "users", ["public_user_id"], unique=True)
    if not has_index("users", "ux_users_username"):
        op.create_index("ux_users_username", "users", ["username"], unique=True)

    add_column_if_missing("job_seeker_profiles", sa.Column("about", sa.Text(), nullable=True))
    add_column_if_missing(
        "job_seeker_profiles",
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="PENDING"),
    )
    add_column_if_missing(
        "job_seeker_profiles",
        sa.Column("certificates_public", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )

    add_column_if_missing("company_profiles", sa.Column("public_company_id", sa.String(length=12), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("slug", sa.String(length=90), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("rating_average", sa.Float(), nullable=True))
    add_column_if_missing("company_profiles", sa.Column("review_count", sa.Integer(), nullable=False, server_default=sa.text("0")))
    backfill_companies()
    if not has_index("company_profiles", "ux_company_profiles_public_company_id"):
        op.create_index("ux_company_profiles_public_company_id", "company_profiles", ["public_company_id"], unique=True)
    if not has_index("company_profiles", "ux_company_profiles_slug"):
        op.create_index("ux_company_profiles_slug", "company_profiles", ["slug"], unique=True)

    add_column_if_missing("jobs", sa.Column("job_public_id", sa.String(length=12), nullable=True))
    backfill_jobs()
    if not has_index("jobs", "ux_jobs_job_public_id"):
        op.create_index("ux_jobs_job_public_id", "jobs", ["job_public_id"], unique=True)

    add_column_if_missing("recruiter_company_members", sa.Column("approved_by_admin_id", sa.Integer(), nullable=True))
    add_column_if_missing("recruiter_company_members", sa.Column("approved_at", sa.DateTime(), nullable=True))
    if has_table("recruiter_company_members") and not has_fk("recruiter_company_members", "fk_recruiter_company_members_approved_by_admin_id_users"):
        op.create_foreign_key(
            "fk_recruiter_company_members_approved_by_admin_id_users",
            "recruiter_company_members",
            "users",
            ["approved_by_admin_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not has_table("user_documents"):
        op.create_table(
            "user_documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_user_id", sa.Integer(), nullable=False),
            sa.Column("document_type", sa.String(length=60), nullable=False),
            sa.Column("file_url", sa.String(length=500), nullable=False),
            sa.Column("original_filename", sa.String(length=255), nullable=True),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="PENDING"),
            sa.Column("reviewed_by", sa.Integer(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("review_note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_user_documents_owner_user_id", "user_documents", ["owner_user_id"], unique=False)
        op.create_index("ix_user_documents_document_type", "user_documents", ["document_type"], unique=False)
        op.create_index("ix_user_documents_verification_status", "user_documents", ["verification_status"], unique=False)


def downgrade() -> None:
    pass
