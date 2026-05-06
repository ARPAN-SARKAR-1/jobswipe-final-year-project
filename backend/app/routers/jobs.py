from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_optional_current_user, require_roles
from app.models.company_profile import CompanyProfile
from app.models.application import Application
from app.models.enums import AccountStatus, JobModerationStatus, RecruiterVerificationStatus, UserRole
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.swipe import Swipe
from app.models.user import User
from app.schemas.job import JobCreate, JobRead, JobUpdate
from app.utils.match_score import calculate_match_score
from app.utils.skills import split_skills

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def apply_job_filters(
    statement,
    job_type: str | None,
    experience_level: str | None,
    location: str | None,
    skill: str | None,
    skills: list[str] | None,
    work_mode: str | None,
    active_only: bool,
):
    statement = statement.where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
    verified_recruiters = select(CompanyProfile.recruiter_id).where(
        CompanyProfile.recruiter_verification_status == RecruiterVerificationStatus.VERIFIED.value
    )
    statement = statement.where(Job.recruiter_id.in_(verified_recruiters))
    if active_only:
        statement = statement.where(Job.is_active.is_(True)).where(Job.deadline >= date.today())
    if job_type:
        statement = statement.where(Job.job_type == job_type)
    if experience_level:
        statement = statement.where(Job.required_experience_level == experience_level)
    if location:
        statement = statement.where(Job.location.ilike(f"%{location}%"))
    skill_filters = split_skills([*(skills or []), skill] if skill else (skills or []))
    if skill_filters:
        statement = statement.where(or_(*[Job.required_skills.ilike(f"%{item}%") for item in skill_filters]))
    if work_mode:
        statement = statement.where(Job.work_mode == work_mode)
    return statement


def apply_job_context(jobs: list[Job], db: Session, user: User | None) -> list[Job]:
    if user is None or user.role != UserRole.JOB_SEEKER.value:
        return jobs
    profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == user.id))
    applications = db.scalars(select(Application).where(Application.job_seeker_id == user.id)).all()
    application_statuses = {application.job_id: application.status for application in applications}
    for job in jobs:
        score = calculate_match_score(job, profile)
        for key, value in score.items():
            setattr(job, key, value)
        setattr(job, "existing_application_status", application_statuses.get(job.id))
    return jobs


def ensure_verified_recruiter(db: Session, recruiter_id: int) -> CompanyProfile:
    company = db.scalar(select(CompanyProfile).where(CompanyProfile.recruiter_id == recruiter_id))
    if company is None or company.recruiter_verification_status != RecruiterVerificationStatus.VERIFIED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your company profile must be verified by admin before posting jobs.",
        )
    return company


@router.get("", response_model=list[JobRead])
def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    job_type: str | None = Query(default=None, alias="jobType"),
    experience_level: str | None = Query(default=None, alias="experienceLevel"),
    location: str | None = None,
    skill: str | None = None,
    skills: list[str] | None = Query(default=None),
    work_mode: str | None = Query(default=None, alias="workMode"),
    active_only: bool = Query(default=True, alias="activeOnly"),
) -> list[Job]:
    statement = apply_job_filters(
        select(Job).order_by(Job.created_at.desc()),
        job_type,
        experience_level,
        location,
        skill,
        skills,
        work_mode,
        active_only,
    )
    return apply_job_context(list(db.scalars(statement).all()), db, current_user)


@router.get("/feed", response_model=list[JobRead])
def job_feed(
    current_user: Annotated[User, Depends(require_roles(UserRole.JOB_SEEKER.value))],
    db: Annotated[Session, Depends(get_db)],
    job_type: str | None = Query(default=None, alias="jobType"),
    experience_level: str | None = Query(default=None, alias="experienceLevel"),
    location: str | None = None,
    skill: str | None = None,
    skills: list[str] | None = Query(default=None),
    work_mode: str | None = Query(default=None, alias="workMode"),
    active_only: bool = Query(default=True, alias="activeOnly"),
) -> list[Job]:
    swiped_job_ids = select(Swipe.job_id).where(Swipe.job_seeker_id == current_user.id)
    applied_job_ids = select(Application.job_id).where(Application.job_seeker_id == current_user.id)
    base_statement = (
        select(Job)
        .where(Job.id.not_in(swiped_job_ids))
        .where(Job.id.not_in(applied_job_ids))
        .order_by(Job.created_at.desc())
        .limit(50)
    )
    statement = apply_job_filters(base_statement, job_type, experience_level, location, skill, skills, work_mode, active_only)

    if not skill and not skills:
        profile = db.scalar(select(JobSeekerProfile).where(JobSeekerProfile.user_id == current_user.id))
        profile_skills = split_skills(profile.skills if profile else None)
        if profile_skills:
            profile_statement = apply_job_filters(
                base_statement,
                job_type,
                experience_level,
                location,
                None,
                profile_skills,
                work_mode,
                active_only,
            )
            matched_jobs = list(db.scalars(profile_statement).all())
            if matched_jobs:
                return apply_job_context(matched_jobs, db, current_user)

    return apply_job_context(list(db.scalars(statement).all()), db, current_user)


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> Job:
    job = db.get(Job, job_id)
    company = db.scalar(select(CompanyProfile).where(CompanyProfile.recruiter_id == job.recruiter_id)) if job else None
    if (
        job is None
        or job.moderation_status != JobModerationStatus.ACTIVE.value
        or company is None
        or company.recruiter_verification_status != RecruiterVerificationStatus.VERIFIED.value
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return apply_job_context([job], db, current_user)[0]


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Job:
    if current_user.account_status == AccountStatus.SUSPENDED.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suspended recruiters cannot post new jobs")
    company = ensure_verified_recruiter(db, current_user.id)
    job = Job(recruiter_id=current_user.id, **payload.model_dump(exclude={"required_skills_list"}))
    if not job.company_logo_url and company and company.company_logo_url:
        job.company_logo_url = company.company_logo_url
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.put("/{job_id}", response_model=JobRead)
def update_job(
    job_id: int,
    payload: JobUpdate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Job:
    job = db.scalar(select(Job).where(Job.id == job_id).where(Job.recruiter_id == current_user.id))
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("is_active") is True:
        ensure_verified_recruiter(db, current_user.id)
    if update_data.get("has_bond") is False:
        update_data["bond_years"] = None
        update_data["bond_details"] = None
    for key, value in update_data.items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    job = db.scalar(select(Job).where(Job.id == job_id).where(Job.recruiter_id == current_user.id))
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job.is_active = False
    db.commit()
    return {"message": "Job deactivated"}
