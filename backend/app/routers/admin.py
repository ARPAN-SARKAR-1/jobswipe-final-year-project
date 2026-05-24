from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import hash_password, require_admin_or_owner, require_owner
from app.models.admin_action_log import AdminActionLog
from app.models.application import Application
from app.models.chat_thread import ChatThread
from app.models.company import Company
from app.models.company_review import CompanyReview
from app.models.enums import (
    AccountStatus,
    ApplicationAdminStatus,
    ChatThreadStatus,
    CompanyVerificationStatus,
    JobModerationStatus,
    RecruiterVerificationStatus,
    ReportStatus,
    UserRole,
)
from app.models.job import Job
from app.models.recruiter_profile import RecruiterProfile
from app.models.report import Report
from app.models.swipe import Swipe
from app.models.user import User
from app.schemas.admin import AdminActionLogRead, AdminCreateRequest, AdminNoteRequest, AdminReasonRequest
from app.schemas.application import ApplicationRead
from app.schemas.chat import ChatThreadRead
from app.schemas.auth import UserRead
from app.schemas.company import AdminCompanyReviewRead, CompanyRead
from app.schemas.job import JobRead
from app.schemas.profile import AdminRecruiterVerificationRead
from app.schemas.report import ReportRead, ReportStatusUpdate
from app.schemas.swipe import SwipeRead
from app.services.company_reviews import recalculate_company_rating
from app.services.notifications import create_notification
from app.services.timeline import add_timeline_event
from app.utils.pagination import LimitQuery, PageQuery, pagination_offset

router = APIRouter(prefix="/admin", tags=["Admin"])


def log_action(
    db: Session,
    admin: User,
    action_type: str,
    target_type: str,
    target_id: int,
    reason: str | None = None,
) -> None:
    db.add(
        AdminActionLog(
            admin_id=admin.id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
        )
    )


def ensure_user_exists(user: User | None) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def ensure_owner_target_allowed(current_user: User, target: User, action: str) -> None:
    if target.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Owner cannot {action} themselves.")
    if target.is_protected_owner or target.role == UserRole.OWNER.value:
        if action == "suspend":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner account cannot be suspended.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Protected Owner cannot be removed.")


def ensure_moderation_target_allowed(current_user: User, target: User, action: str) -> None:
    if target.is_protected_owner or target.role == UserRole.OWNER.value:
        if action == "suspend":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner account cannot be suspended.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner account cannot be managed.")
    if current_user.role == UserRole.ADMIN.value and target.role == UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot manage other admins.")
    if target.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot suspend their own account")


@router.get("/dashboard")
def dashboard(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    total_users = db.scalar(select(func.count(User.id))) or 0
    total_job_seekers = db.scalar(select(func.count(User.id)).where(User.role == UserRole.JOB_SEEKER.value)) or 0
    total_recruiters = db.scalar(select(func.count(User.id)).where(User.role == UserRole.RECRUITER.value)) or 0
    total_jobs = db.scalar(select(func.count(Job.id))) or 0
    active_jobs = db.scalar(
        select(func.count(Job.id))
        .where(Job.is_active.is_(True))
        .where(Job.deadline >= date.today())
        .where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
    ) or 0
    expired_jobs = db.scalar(select(func.count(Job.id)).where(Job.deadline < date.today())) or 0
    total_applications = db.scalar(select(func.count(Application.id))) or 0
    return {
        "total_users": total_users,
        "total_job_seekers": total_job_seekers,
        "total_recruiters": total_recruiters,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "expired_jobs": expired_jobs,
        "total_applications": total_applications,
    }


@router.get("/users", response_model=list[UserRead])
def users(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[User]:
    statement = select(User).order_by(User.created_at.desc())
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(User.name.ilike(term), User.email.ilike(term), User.role.ilike(term)))
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/jobs", response_model=list[JobRead])
def jobs(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[Job]:
    statement = select(Job).order_by(Job.created_at.desc())
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Job.title.ilike(term), Job.company_name.ilike(term), Job.location.ilike(term)))
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/applications", response_model=list[ApplicationRead])
def applications(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[Application]:
    statement = (
        select(Application)
        .options(joinedload(Application.job), joinedload(Application.chat_thread))
        .order_by(Application.created_at.desc())
    )
    if search:
        term = f"%{search.strip()}%"
        statement = statement.join(Job, Application.job_id == Job.id).where(or_(Job.title.ilike(term), Job.company_name.ilike(term)))
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    return list(
        db.scalars(
            statement
        ).all()
    )


@router.get("/chats", response_model=list[ChatThreadRead])
def chats(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
) -> list[ChatThread]:
    return list(
        db.scalars(
            select(ChatThread)
            .options(
                joinedload(ChatThread.application),
                joinedload(ChatThread.job),
                joinedload(ChatThread.recruiter),
                joinedload(ChatThread.job_seeker),
            )
            .order_by(ChatThread.created_at.desc())
            .offset(pagination_offset(page, limit))
            .limit(limit)
        ).all()
    )


@router.get("/swipes", response_model=list[SwipeRead])
def swipes(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
) -> list[Swipe]:
    return list(
        db.scalars(
            select(Swipe)
            .options(joinedload(Swipe.job))
            .order_by(Swipe.created_at.desc())
            .offset(pagination_offset(page, limit))
            .limit(limit)
        ).all()
    )


@router.get("/reports", response_model=list[ReportRead])
def reports(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[Report]:
    statement = (
        select(Report)
        .options(joinedload(Report.reporter), joinedload(Report.recruiter), joinedload(Report.job))
        .order_by(Report.created_at.desc(), Report.id.desc())
    )
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Report.report_type.ilike(term), Report.description.ilike(term), Report.status.ilike(term)))
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    return list(
        db.scalars(
            statement
        ).all()
    )


@router.put("/reports/{report_id}/status", response_model=ReportRead)
def update_report_status(
    report_id: int,
    payload: ReportStatusUpdate,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> Report:
    report = db.scalar(
        select(Report)
        .options(joinedload(Report.reporter), joinedload(Report.recruiter), joinedload(Report.job))
        .where(Report.id == report_id)
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    report.status = payload.status.value
    report.admin_note = payload.admin_note
    create_notification(
        db,
        report.reporter_id,
        "Report updated",
        f"Your report has been marked {payload.status.value.lower()}.",
        "ADMIN_ACTION",
        "/jobseeker/applications",
    )
    log_action(db, current_user, f"REPORT_{payload.status.value}", "REPORT", report.id, payload.admin_note)
    db.commit()
    db.refresh(report)
    return report


@router.get("/action-logs", response_model=list[AdminActionLogRead])
def action_logs(
    _current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AdminActionLog]:
    return list(db.scalars(select(AdminActionLog).order_by(AdminActionLog.created_at.desc()).limit(200)).all())


@router.get("/admins", response_model=list[UserRead])
def list_admins(
    _current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .where(User.role.in_([UserRole.ADMIN.value, UserRole.OWNER.value]))
            .order_by(User.role.desc(), User.created_at.desc())
        ).all()
    )


def company_admin_response(db: Session, company: Company) -> CompanyRead:
    active_jobs = db.scalar(
        select(func.count(Job.id))
        .where(Job.company_id == company.id)
        .where(Job.is_active.is_(True))
        .where(Job.deadline >= date.today())
        .where(Job.moderation_status == JobModerationStatus.ACTIVE.value)
    ) or 0
    recruiter_count = db.scalar(select(func.count(RecruiterProfile.id)).where(RecruiterProfile.company_id == company.id)) or 0
    return CompanyRead(
        id=company.id,
        company_name=company.company_name,
        company_logo_url=company.company_logo_url,
        company_type=company.company_type,
        industry=company.industry,
        website=company.website,
        official_email_domain=company.official_email_domain,
        description=company.description,
        headquarters_location=company.headquarters_location,
        founded_year=company.founded_year,
        company_size=company.company_size,
        registration_number=company.registration_number,
        verification_status=company.verification_status,
        verification_note=company.verification_note,
        verified_by_admin_id=company.verified_by_admin_id,
        verified_at=company.verified_at,
        average_rating=company.average_rating,
        total_reviews=company.total_reviews,
        active_jobs_count=active_jobs,
        recruiter_count=recruiter_count,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def recruiter_verification_response(profile: RecruiterProfile) -> AdminRecruiterVerificationRead:
    company = profile.company
    return AdminRecruiterVerificationRead(
        id=profile.id,
        recruiter_id=profile.user_id,
        company_id=profile.company_id,
        company_name=company.company_name if company else None,
        company_logo_url=company.company_logo_url if company else None,
        company_type=company.company_type if company else None,
        industry=company.industry if company else None,
        website=company.website if company else None,
        official_email_domain=company.official_email_domain if company else None,
        description=company.description if company else None,
        headquarters_location=company.headquarters_location if company else None,
        location=company.headquarters_location if company else None,
        founded_year=company.founded_year if company else None,
        company_size=company.company_size if company else None,
        registration_number=company.registration_number if company else None,
        verification_status=company.verification_status if company else CompanyVerificationStatus.PENDING.value,
        company_verification_note=company.verification_note if company else None,
        company_verified_at=company.verified_at if company else None,
        company_verified_by_admin_id=company.verified_by_admin_id if company else None,
        average_rating=company.average_rating if company else 0,
        total_reviews=company.total_reviews if company else 0,
        designation=profile.designation,
        department=profile.department,
        official_email=profile.official_email,
        recruiter_verification_status=profile.recruiter_verification_status,
        verification_note=profile.verification_note,
        verified_at=profile.verified_at,
        verified_by_admin_id=profile.verified_by_admin_id,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        recruiter_name=profile.recruiter.name,
        recruiter_email=profile.recruiter.email,
        account_status=profile.recruiter.account_status,
    )


@router.get("/companies", response_model=list[CompanyRead])
def company_verifications(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[CompanyRead]:
    statement = select(Company).order_by(Company.verification_status.asc(), Company.updated_at.desc())
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Company.company_name.ilike(term),
                Company.industry.ilike(term),
                Company.company_type.ilike(term),
                Company.website.ilike(term),
            )
        )
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    companies = db.scalars(statement).all()
    return [company_admin_response(db, company) for company in companies]


@router.put("/companies/{company_id}/verify", response_model=CompanyRead)
def verify_company(
    company_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyRead:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company.verification_status = CompanyVerificationStatus.VERIFIED.value
    company.verification_note = payload.admin_note
    company.verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
    company.verified_by_admin_id = current_user.id
    recruiters = db.scalars(select(RecruiterProfile).where(RecruiterProfile.company_id == company.id)).all()
    for profile in recruiters:
        create_notification(
            db,
            profile.user_id,
            "Company verified",
            f"{company.company_name} is verified. Recruiters still need recruiter verification before posting public jobs.",
            "COMPANY_VERIFIED",
            "/recruiter/dashboard",
        )
    log_action(db, current_user, "VERIFY_COMPANY", "COMPANY", company.id, payload.admin_note)
    db.commit()
    db.refresh(company)
    return company_admin_response(db, company)


@router.put("/companies/{company_id}/reject", response_model=CompanyRead)
def reject_company(
    company_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyRead:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company.verification_status = CompanyVerificationStatus.REJECTED.value
    company.verification_note = payload.admin_note
    company.verified_at = None
    company.verified_by_admin_id = current_user.id
    recruiters = db.scalars(select(RecruiterProfile).where(RecruiterProfile.company_id == company.id)).all()
    for profile in recruiters:
        create_notification(
            db,
            profile.user_id,
            "Company verification rejected",
            f"{company.company_name} was rejected: {payload.admin_note}",
            "COMPANY_REJECTED",
            "/recruiter/company",
        )
    log_action(db, current_user, "REJECT_COMPANY", "COMPANY", company.id, payload.admin_note)
    db.commit()
    db.refresh(company)
    return company_admin_response(db, company)


@router.get("/recruiter-verifications", response_model=list[AdminRecruiterVerificationRead])
def recruiter_verifications(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[AdminRecruiterVerificationRead]:
    statement = (
        select(RecruiterProfile)
        .join(User, RecruiterProfile.user_id == User.id)
        .outerjoin(Company, RecruiterProfile.company_id == Company.id)
        .options(joinedload(RecruiterProfile.recruiter), joinedload(RecruiterProfile.company))
        .where(User.role == UserRole.RECRUITER.value)
        .order_by(RecruiterProfile.recruiter_verification_status.asc(), RecruiterProfile.updated_at.desc())
    )
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(User.name.ilike(term), User.email.ilike(term), Company.company_name.ilike(term)))
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    profiles = db.scalars(statement).all()
    return [recruiter_verification_response(profile) for profile in profiles]


@router.get("/recruiters", response_model=list[AdminRecruiterVerificationRead])
def recruiters(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[AdminRecruiterVerificationRead]:
    return recruiter_verifications(_current_user, db, page, limit, search)


def find_recruiter_profile(db: Session, recruiter_id: int) -> RecruiterProfile:
    profile = db.scalar(
        select(RecruiterProfile)
        .options(joinedload(RecruiterProfile.recruiter), joinedload(RecruiterProfile.company))
        .where((RecruiterProfile.id == recruiter_id) | (RecruiterProfile.user_id == recruiter_id))
    )
    if profile is None or profile.recruiter.role != UserRole.RECRUITER.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")
    return profile


@router.put("/recruiters/{recruiter_id}/verify", response_model=AdminRecruiterVerificationRead)
def verify_recruiter(
    recruiter_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminRecruiterVerificationRead:
    profile = find_recruiter_profile(db, recruiter_id)
    profile.recruiter_verification_status = RecruiterVerificationStatus.VERIFIED.value
    profile.verification_note = payload.admin_note
    profile.verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
    profile.verified_by_admin_id = current_user.id
    create_notification(
        db,
        profile.user_id,
        "Recruiter verified",
        "Your recruiter profile has been verified. You can post active jobs once your company is verified.",
        "RECRUITER_VERIFIED",
        "/recruiter/dashboard",
    )
    log_action(db, current_user, "VERIFY_RECRUITER", "USER", profile.user_id, payload.admin_note)
    db.commit()
    db.refresh(profile)
    return recruiter_verification_response(profile)


@router.put("/recruiters/{recruiter_id}/reject", response_model=AdminRecruiterVerificationRead)
def reject_recruiter(
    recruiter_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminRecruiterVerificationRead:
    profile = find_recruiter_profile(db, recruiter_id)
    profile.recruiter_verification_status = RecruiterVerificationStatus.REJECTED.value
    profile.verification_note = payload.admin_note
    profile.verified_at = None
    profile.verified_by_admin_id = current_user.id
    create_notification(
        db,
        profile.user_id,
        "Recruiter verification rejected",
        f"Your recruiter verification was rejected: {payload.admin_note}",
        "RECRUITER_REJECTED",
        "/recruiter/company",
    )
    log_action(db, current_user, "REJECT_RECRUITER", "USER", profile.user_id, payload.admin_note)
    db.commit()
    db.refresh(profile)
    return recruiter_verification_response(profile)


def company_review_response(review: CompanyReview) -> AdminCompanyReviewRead:
    return AdminCompanyReviewRead(
        id=review.id,
        company_id=review.company_id,
        job_seeker_id=review.job_seeker_id,
        rating=review.rating,
        review_text=review.review_text,
        is_visible=review.is_visible,
        reviewer_name=review.job_seeker.name if review.job_seeker else None,
        reviewer_email=review.job_seeker.email if review.job_seeker else None,
        company_name=review.company.company_name if review.company else None,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.get("/company-reviews", response_model=list[AdminCompanyReviewRead])
def company_reviews(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[AdminCompanyReviewRead]:
    statement = (
        select(CompanyReview)
        .join(Company, CompanyReview.company_id == Company.id)
        .join(User, CompanyReview.job_seeker_id == User.id)
        .options(joinedload(CompanyReview.company), joinedload(CompanyReview.job_seeker))
        .order_by(CompanyReview.created_at.desc(), CompanyReview.id.desc())
    )
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Company.company_name.ilike(term), User.name.ilike(term), User.email.ilike(term)))
    statement = statement.offset(pagination_offset(page, limit)).limit(limit)
    reviews = db.scalars(statement).all()
    return [company_review_response(review) for review in reviews]


@router.put("/company-reviews/{review_id}/hide", response_model=AdminCompanyReviewRead)
def hide_company_review(
    review_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminCompanyReviewRead:
    review = db.scalar(
        select(CompanyReview)
        .options(joinedload(CompanyReview.company), joinedload(CompanyReview.job_seeker))
        .where(CompanyReview.id == review_id)
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    review.is_visible = False
    recalculate_company_rating(db, review.company_id)
    log_action(db, current_user, "HIDE_COMPANY_REVIEW", "COMPANY_REVIEW", review.id)
    db.commit()
    db.refresh(review)
    return company_review_response(review)


@router.put("/company-reviews/{review_id}/show", response_model=AdminCompanyReviewRead)
def show_company_review(
    review_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminCompanyReviewRead:
    review = db.scalar(
        select(CompanyReview)
        .options(joinedload(CompanyReview.company), joinedload(CompanyReview.job_seeker))
        .where(CompanyReview.id == review_id)
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    review.is_visible = True
    recalculate_company_rating(db, review.company_id)
    log_action(db, current_user, "SHOW_COMPANY_REVIEW", "COMPANY_REVIEW", review.id)
    db.commit()
    db.refresh(review)
    return company_review_response(review)


@router.post("/admins", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: AdminCreateRequest,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=UserRole.ADMIN.value,
        accepted_terms=True,
        accepted_terms_at=datetime.now(timezone.utc).replace(tzinfo=None),
        account_status=AccountStatus.ACTIVE.value,
        is_protected_owner=False,
    )
    db.add(user)
    db.flush()
    log_action(db, current_user, "CREATE_ADMIN", "USER", user.id, "Owner created admin account")
    db.commit()
    db.refresh(user)
    return user


@router.put("/admins/{admin_id}/suspend", response_model=UserRead)
def suspend_admin(
    admin_id: int,
    payload: AdminReasonRequest,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    target = ensure_user_exists(db.get(User, admin_id))
    ensure_owner_target_allowed(current_user, target, "suspend")
    if target.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only ADMIN accounts can be managed here.")

    target.account_status = AccountStatus.SUSPENDED.value
    target.suspension_reason = payload.reason
    log_action(db, current_user, "SUSPEND_ADMIN", "USER", target.id, payload.reason)
    db.commit()
    db.refresh(target)
    return target


@router.put("/admins/{admin_id}/activate", response_model=UserRead)
def activate_admin(
    admin_id: int,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    target = ensure_user_exists(db.get(User, admin_id))
    ensure_owner_target_allowed(current_user, target, "activate")
    if target.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only ADMIN accounts can be managed here.")

    target.account_status = AccountStatus.ACTIVE.value
    target.suspension_reason = None
    log_action(db, current_user, "ACTIVATE_ADMIN", "USER", target.id)
    db.commit()
    db.refresh(target)
    return target


@router.put("/admins/{admin_id}/remove", response_model=UserRead)
def remove_admin(
    admin_id: int,
    payload: AdminReasonRequest,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    target = ensure_user_exists(db.get(User, admin_id))
    ensure_owner_target_allowed(current_user, target, "remove")
    if target.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only ADMIN accounts can be managed here.")

    target.account_status = AccountStatus.SUSPENDED.value
    target.suspension_reason = f"Removed by owner: {payload.reason}"
    log_action(db, current_user, "REMOVE_ADMIN", "USER", target.id, payload.reason)
    db.commit()
    db.refresh(target)
    return target


@router.put("/users/{user_id}/suspend", response_model=UserRead)
def suspend_user(
    user_id: int,
    payload: AdminReasonRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = ensure_user_exists(db.get(User, user_id))
    ensure_moderation_target_allowed(current_user, user, "suspend")

    user.account_status = AccountStatus.SUSPENDED.value
    user.suspension_reason = payload.reason
    log_action(db, current_user, "SUSPEND_USER", "USER", user.id, payload.reason)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/activate", response_model=UserRead)
def activate_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = ensure_user_exists(db.get(User, user_id))
    ensure_moderation_target_allowed(current_user, user, "activate")

    user.account_status = AccountStatus.ACTIVE.value
    user.suspension_reason = None
    log_action(db, current_user, "ACTIVATE_USER", "USER", user.id)
    db.commit()
    db.refresh(user)
    return user


@router.put("/jobs/{job_id}/pause", response_model=JobRead)
def pause_job(
    job_id: int,
    payload: AdminReasonRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job.moderation_status = JobModerationStatus.PAUSED.value
    job.moderation_reason = payload.reason
    create_notification(
        db,
        job.recruiter_id,
        "Job paused by admin",
        f"Your job post '{job.title}' was paused: {payload.reason}",
        "JOB_PAUSED",
        "/recruiter/dashboard",
    )
    log_action(db, current_user, "PAUSE_JOB", "JOB", job.id, payload.reason)
    db.commit()
    db.refresh(job)
    return job


@router.put("/jobs/{job_id}/activate", response_model=JobRead)
def activate_job(
    job_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job.moderation_status = JobModerationStatus.ACTIVE.value
    job.moderation_reason = None
    log_action(db, current_user, "ACTIVATE_JOB", "JOB", job.id)
    db.commit()
    db.refresh(job)
    return job


@router.put("/jobs/{job_id}/remove", response_model=JobRead)
def remove_job(
    job_id: int,
    payload: AdminReasonRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job.moderation_status = JobModerationStatus.REMOVED.value
    job.moderation_reason = payload.reason
    create_notification(
        db,
        job.recruiter_id,
        "Job removed by admin",
        f"Your job post '{job.title}' was removed: {payload.reason}",
        "JOB_PAUSED",
        "/recruiter/dashboard",
    )
    log_action(db, current_user, "REMOVE_JOB", "JOB", job.id, payload.reason)
    db.commit()
    db.refresh(job)
    return job


@router.put("/applications/{application_id}/pause", response_model=ApplicationRead)
def pause_application(
    application_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> Application:
    application = db.scalar(
        select(Application).options(joinedload(Application.job)).where(Application.id == application_id)
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    application.admin_status = ApplicationAdminStatus.PAUSED.value
    application.admin_note = payload.admin_note
    add_timeline_event(
        db,
        application.id,
        "ADMIN_PAUSED",
        old_status=application.status,
        new_status=application.status,
        note=payload.admin_note,
        created_by_user_id=current_user.id,
    )
    log_action(db, current_user, "PAUSE_APPLICATION", "APPLICATION", application.id, payload.admin_note)
    db.commit()
    db.refresh(application)
    return application


@router.put("/applications/{application_id}/activate", response_model=ApplicationRead)
def activate_application(
    application_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> Application:
    application = db.scalar(
        select(Application).options(joinedload(Application.job)).where(Application.id == application_id)
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    application.admin_status = ApplicationAdminStatus.ACTIVE.value
    application.admin_note = None
    add_timeline_event(
        db,
        application.id,
        "ADMIN_ACTIVATED",
        old_status=application.status,
        new_status=application.status,
        note="Application moderation restored",
        created_by_user_id=current_user.id,
    )
    log_action(db, current_user, "ACTIVATE_APPLICATION", "APPLICATION", application.id)
    db.commit()
    db.refresh(application)
    return application


@router.put("/chats/{thread_id}/pause", response_model=ChatThreadRead)
def pause_chat(
    thread_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatThread:
    thread = db.scalar(
        select(ChatThread)
        .options(
            joinedload(ChatThread.application),
            joinedload(ChatThread.job),
            joinedload(ChatThread.recruiter),
            joinedload(ChatThread.job_seeker),
        )
        .where(ChatThread.id == thread_id)
    )
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat thread not found")

    thread.status = ChatThreadStatus.PAUSED.value
    log_action(db, current_user, "PAUSE_CHAT", "CHAT_THREAD", thread.id, "Chat paused by admin")
    db.commit()
    db.refresh(thread)
    return thread


@router.put("/chats/{thread_id}/activate", response_model=ChatThreadRead)
def activate_chat(
    thread_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatThread:
    thread = db.scalar(
        select(ChatThread)
        .options(
            joinedload(ChatThread.application),
            joinedload(ChatThread.job),
            joinedload(ChatThread.recruiter),
            joinedload(ChatThread.job_seeker),
        )
        .where(ChatThread.id == thread_id)
    )
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat thread not found")

    thread.status = ChatThreadStatus.ACTIVE.value
    log_action(db, current_user, "ACTIVATE_CHAT", "CHAT_THREAD", thread.id)
    db.commit()
    db.refresh(thread)
    return thread
