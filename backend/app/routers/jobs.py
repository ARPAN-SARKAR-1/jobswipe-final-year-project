from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_optional_current_user, require_roles
from app.models.application import Application
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.enums import (
    AccountStatus,
    CompanyMemberRole,
    CompanyVerificationStatus,
    JobModerationStatus,
    RecruiterVerificationStatus,
    UserRole,
)
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.recruiter_profile import RecruiterProfile
from app.models.swipe import Swipe
from app.models.user import User
from app.schemas.job import JobCreate, JobRead, JobUpdate
from app.services.job_visibility import ensure_public_job_available
from app.services.risk_assessment import assess_job_risk
from app.services.user_risk_assessment import update_user_risk
from app.utils.match_score import calculate_match_score
from app.utils.pagination import LimitQuery, PageQuery, pagination_offset
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
    statement = (
        statement.join(RecruiterProfile, Job.recruiter_id == RecruiterProfile.user_id)
        .join(Company, Job.company_id == Company.id)
        .join(User, Job.recruiter_id == User.id)
        .where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
        .where(Job.company_id == RecruiterProfile.company_id)
        .where(RecruiterProfile.recruiter_verification_status == RecruiterVerificationStatus.VERIFIED.value)
        .where(Company.verification_status == CompanyVerificationStatus.VERIFIED.value)
        .where(User.account_status == AccountStatus.ACTIVE.value)
    )
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


def ensure_recruiter_can_publish(db: Session, recruiter: User) -> tuple[RecruiterProfile, Company]:
    if recruiter.account_status != AccountStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter account must be active before posting jobs.")
    profile = db.scalar(
        select(RecruiterProfile)
        .where(RecruiterProfile.user_id == recruiter.id)
        .options(joinedload(RecruiterProfile.company))
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your recruiter profile must be verified before posting jobs.",
        )
    if profile.recruiter_verification_status != RecruiterVerificationStatus.VERIFIED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your recruiter profile must be verified before posting jobs.",
        )
    if profile.company is None or profile.company.verification_status != CompanyVerificationStatus.VERIFIED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your company must be verified before posting jobs.",
        )
    member = db.scalar(
        select(CompanyMember)
        .where(CompanyMember.company_id == profile.company_id)
        .where(CompanyMember.user_id == recruiter.id)
        .where(CompanyMember.verification_status == RecruiterVerificationStatus.VERIFIED.value)
        .where(
            CompanyMember.company_role.in_(
                [
                    CompanyMemberRole.COMPANY_OWNER.value,
                    CompanyMemberRole.COMPANY_ADMIN.value,
                    CompanyMemberRole.COMPANY_RECRUITER.value,
                ]
            )
        )
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your company membership must be approved before posting jobs.",
        )
    if not profile.company.company_name:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Complete your company profile before posting jobs.")
    return profile, profile.company


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
    page: PageQuery = 1,
    limit: LimitQuery = 20,
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
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
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
    job = ensure_public_job_available(db, db.get(Job, job_id), "Job not found", not_found=True)
    return apply_job_context([job], db, current_user)[0]


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> Job:
    profile: RecruiterProfile | None = None
    company: Company | None = None
    if payload.is_active:
        profile, company = ensure_recruiter_can_publish(db, current_user)
    else:
        profile = db.scalar(
            select(RecruiterProfile)
            .where(RecruiterProfile.user_id == current_user.id)
            .options(joinedload(RecruiterProfile.company))
        )
        company = profile.company if profile else None
    if company is None or profile is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your company must be verified before posting jobs.")
    data = payload.model_dump(exclude={"required_skills_list"})
    data["company_id"] = company.id
    data["company_name"] = company.company_name
    data["company_logo_url"] = company.company_logo_url or data.get("company_logo_url")
    job = Job(recruiter_id=current_user.id, **data)
    db.add(job)
    db.flush()
    assessment = assess_job_risk(db, job)
    update_user_risk(db, current_user)
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
    will_be_active = update_data.get("is_active", job.is_active)
    profile: RecruiterProfile | None = None
    company: Company | None = None
    if will_be_active:
        profile, company = ensure_recruiter_can_publish(db, current_user)
    elif "company_name" in update_data or "company_logo_url" in update_data:
        profile = db.scalar(
            select(RecruiterProfile)
            .where(RecruiterProfile.user_id == current_user.id)
            .options(joinedload(RecruiterProfile.company))
        )
        company = profile.company if profile else None
    if company is not None:
        update_data["company_id"] = company.id
        update_data["company_name"] = company.company_name
        update_data["company_logo_url"] = company.company_logo_url or update_data.get("company_logo_url") or job.company_logo_url
    if update_data.get("has_bond") is False:
        update_data["bond_years"] = None
        update_data["bond_details"] = None
    for key, value in update_data.items():
        setattr(job, key, value)
    db.flush()
    assessment = assess_job_risk(db, job)
    update_user_risk(db, current_user)
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
