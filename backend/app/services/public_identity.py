from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company_profile import CompanyProfile
from app.models.job import Job
from app.models.user import User
from app.utils.public_identity import generate_public_id, normalize_username, slugify, username_seed


def _unique_public_id(db: Session, model, column_name: str, prefix: str) -> str:
    column = getattr(model, column_name)
    for _ in range(20):
        candidate = generate_public_id(prefix)
        if db.scalar(select(model).where(column == candidate)) is None:
            return candidate
    raise RuntimeError("Could not generate a unique public identifier.")


def unique_user_public_id(db: Session) -> str:
    return _unique_public_id(db, User, "public_user_id", "SFS")


def unique_company_public_id(db: Session) -> str:
    return _unique_public_id(db, CompanyProfile, "public_company_id", "CMP")


def unique_job_public_id(db: Session) -> str:
    return _unique_public_id(db, Job, "job_public_id", "JOB")


def unique_username(db: Session, seed: str) -> str:
    base = username_seed(seed)
    for index in range(100):
        candidate = base if index == 0 else f"{base[: max(3, 29 - len(str(index)))]}-{index}"
        try:
            candidate = normalize_username(candidate)
        except ValueError:
            candidate = normalize_username(f"user-{index + 1}")
        if db.scalar(select(User).where(User.username == candidate)) is None:
            return candidate
    raise RuntimeError("Could not generate a unique username.")


def unique_company_slug(db: Session, name: str | None) -> str:
    base = slugify(name, fallback="company")
    for index in range(100):
        candidate = base if index == 0 else f"{base[: max(3, 78 - len(str(index)))]}-{index}"
        if db.scalar(select(CompanyProfile).where(CompanyProfile.slug == candidate)) is None:
            return candidate
    raise RuntimeError("Could not generate a unique company slug.")


def ensure_user_public_identity(db: Session, user: User) -> bool:
    changed = False
    if not getattr(user, "public_user_id", None):
        user.public_user_id = unique_user_public_id(db)
        changed = True
    if not getattr(user, "username", None):
        seed = user.email.split("@", 1)[0] if user.email else user.name
        user.username = unique_username(db, seed)
        changed = True
    return changed


def ensure_company_public_identity(db: Session, company: CompanyProfile) -> bool:
    changed = False
    if not getattr(company, "public_company_id", None):
        company.public_company_id = unique_company_public_id(db)
        changed = True
    if not getattr(company, "slug", None):
        company.slug = unique_company_slug(db, company.company_name)
        changed = True
    return changed


def ensure_job_public_identity(db: Session, job: Job) -> bool:
    if getattr(job, "job_public_id", None):
        return False
    job.job_public_id = unique_job_public_id(db)
    return True
