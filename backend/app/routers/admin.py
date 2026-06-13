from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.core.security import hash_password, require_admin_or_owner, require_owner
from app.models.admin_action_log import AdminActionLog
from app.models.application import Application
from app.models.chat_thread import ChatThread
from app.models.company_profile import CompanyProfile
from app.models.company_review import CompanyReview
from app.models.enums import (
    AccountStatus,
    ApplicationAdminStatus,
    ChatThreadStatus,
    CompanyJoinStatus,
    CompanyVerificationStatus,
    DocumentVerificationStatus,
    JobModerationStatus,
    JobSeekerVerificationStatus,
    RecruiterVerificationStatus,
    ReviewModerationStatus,
    ReportStatus,
    UserRole,
)
from app.models.job import Job
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.recruiter_company_member import RecruiterCompanyMember
from app.models.report import Report
from app.models.swipe import Swipe
from app.models.user import User
from app.models.user_document import UserDocument
from app.schemas.admin import AdminActionLogRead, AdminCreateRequest, AdminNoteRequest, AdminReasonRequest
from app.schemas.application import ApplicationRead
from app.schemas.chat import ChatThreadRead
from app.schemas.auth import UserRead
from app.schemas.company import CompanyReviewModerationRequest, CompanyReviewRead, RecruiterCompanyMemberRead
from app.schemas.job import JobRead
from app.schemas.profile import AdminRecruiterVerificationRead
from app.schemas.public_profile import AdminUserDocumentRead, DocumentReviewRequest
from app.schemas.report import ReportRead, ReportStatusUpdate
from app.schemas.swipe import SwipeRead
from app.services.notifications import create_notification
from app.services.public_identity import ensure_user_public_identity
from app.services.timeline import add_timeline_event
from app.services.trust import attach_job_trust, get_or_create_recruiter_membership

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
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


@router.get("/users/search")
def search_users(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(default=None, max_length=100),
    role: str | None = Query(default=None, max_length=30),
    status_filter: str | None = Query(default=None, alias="status", max_length=30),
    protection: str | None = Query(default=None, max_length=20),
    email_verified: str | None = Query(default=None, max_length=20),
    sort_by: str = Query(default="created_at", max_length=30),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    statement = select(User)
    if q:
        pattern = f"%{q.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(User.name).like(pattern),
                func.lower(User.email).like(pattern),
                func.lower(User.public_user_id).like(pattern),
                func.lower(User.username).like(pattern),
            )
        )
    if role:
        statement = statement.where(User.role == role.strip().upper())
    if status_filter:
        statement = statement.where(User.account_status == status_filter.strip().upper())
    if protection == "PROTECTED":
        statement = statement.where(User.is_protected_owner.is_(True))
    elif protection == "NORMAL":
        statement = statement.where(User.is_protected_owner.is_(False))
    if email_verified == "VERIFIED":
        statement = statement.where(User.email_verified.is_(True))
    elif email_verified == "NOT_VERIFIED":
        statement = statement.where(User.email_verified.is_(False))

    sort_columns = {
        "created_at": User.created_at,
        "name": User.name,
        "role": User.role,
        "status": User.account_status,
        "email": User.email,
    }
    sort_column = sort_columns.get(sort_by, User.created_at)
    order = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    users_page = list(db.scalars(statement.order_by(order, User.id.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return {
        "items": [UserRead.model_validate(user).model_dump(mode="json") for user in users_page],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/jobs", response_model=list[JobRead])
def jobs(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Job]:
    return [attach_job_trust(db, job) for job in db.scalars(select(Job).order_by(Job.created_at.desc())).all()]


@router.get("/applications", response_model=list[ApplicationRead])
def applications(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Application]:
    return list(
        db.scalars(
            select(Application)
            .options(joinedload(Application.job), joinedload(Application.chat_thread))
            .order_by(Application.created_at.desc())
        ).all()
    )


@router.get("/chats", response_model=list[ChatThreadRead])
def chats(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
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
        ).all()
    )


@router.get("/swipes", response_model=list[SwipeRead])
def swipes(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Swipe]:
    return list(db.scalars(select(Swipe).options(joinedload(Swipe.job)).order_by(Swipe.created_at.desc())).all())


@router.get("/reports", response_model=list[ReportRead])
def reports(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Report]:
    return list(
        db.scalars(
            select(Report)
            .options(joinedload(Report.reporter), joinedload(Report.recruiter), joinedload(Report.job))
            .order_by(Report.created_at.desc(), Report.id.desc())
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


def recruiter_verification_response(company: CompanyProfile) -> AdminRecruiterVerificationRead:
    membership = company.members[0] if company.members else None
    return AdminRecruiterVerificationRead(
        id=company.id,
        recruiter_id=company.recruiter_id,
        company_name=company.company_name,
        name=company.company_name,
        company_logo_url=company.company_logo_url,
        logo_url=company.company_logo_url,
        website=company.website,
        industry=company.industry,
        company_type=company.company_type,
        description=company.description,
        location=company.location,
        official_email_domain=company.official_email_domain,
        verification_status=company.verification_status,
        recruiter_verification_status=(membership.verification_status if membership else company.recruiter_verification_status),
        company_join_status=(membership.company_join_status if membership else CompanyJoinStatus.PENDING.value),
        designation=(membership.designation if membership else None),
        work_email=(membership.work_email if membership else None),
        verification_note=company.verification_note,
        verified_at=company.verified_at,
        verified_by_admin_id=company.verified_by_admin_id,
        created_at=company.created_at,
        updated_at=company.updated_at,
        recruiter_name=company.recruiter.name,
        recruiter_email=company.recruiter.email,
        account_status=company.recruiter.account_status,
        membership_id=(membership.id if membership else None),
        member_verification_status=(membership.verification_status if membership else RecruiterVerificationStatus.PENDING.value),
        member_join_status=(membership.company_join_status if membership else CompanyJoinStatus.PENDING.value),
        member_admin_note=(membership.admin_note if membership else None),
    )


def membership_response(member: RecruiterCompanyMember) -> RecruiterCompanyMemberRead:
    return RecruiterCompanyMemberRead(
        id=member.id,
        recruiter_id=member.recruiter_id,
        company_id=member.company_id,
        recruiter_name=member.recruiter.name if member.recruiter else None,
        recruiter_email=member.recruiter.email if member.recruiter else None,
        company_name=member.company.company_name if member.company else None,
        designation=member.designation,
        work_email=member.work_email,
        verification_status=member.verification_status,
        company_join_status=member.company_join_status,
        verified_at=member.verified_at,
        verified_by_admin_id=member.verified_by_admin_id,
        verified_by_company_owner_id=member.verified_by_company_owner_id,
        approved_by_admin_id=member.approved_by_admin_id,
        approved_at=member.approved_at,
        admin_note=member.admin_note,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def review_response(review: CompanyReview) -> CompanyReviewRead:
    return CompanyReviewRead(
        id=review.id,
        company_id=review.company_id,
        reviewer_user_id=review.reviewer_user_id,
        reviewer_name=review.reviewer.name if review.reviewer else None,
        application_id=review.application_id,
        rating=review.rating,
        title=review.title,
        review_text=review.review_text,
        work_culture_rating=review.work_culture_rating,
        interview_process_rating=review.interview_process_rating,
        growth_rating=review.growth_rating,
        is_visible=review.is_visible,
        is_flagged=review.is_flagged,
        moderation_status=review.moderation_status,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.get("/recruiter-verifications", response_model=list[AdminRecruiterVerificationRead])
def recruiter_verifications(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AdminRecruiterVerificationRead]:
    companies = db.scalars(
        select(CompanyProfile)
        .join(User, CompanyProfile.recruiter_id == User.id)
        .options(joinedload(CompanyProfile.recruiter), selectinload(CompanyProfile.members))
        .where(User.role == UserRole.RECRUITER.value)
        .order_by(CompanyProfile.verification_status.asc(), CompanyProfile.updated_at.desc())
    ).all()
    return [recruiter_verification_response(company) for company in companies]


@router.put("/recruiters/{recruiter_id}/verify", response_model=AdminRecruiterVerificationRead)
def verify_recruiter(
    recruiter_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminRecruiterVerificationRead:
    company = db.scalar(
        select(CompanyProfile)
        .options(joinedload(CompanyProfile.recruiter), selectinload(CompanyProfile.members))
        .where(CompanyProfile.recruiter_id == recruiter_id)
    )
    if company is None or company.recruiter.role != UserRole.RECRUITER.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")

    membership = get_or_create_recruiter_membership(db, company.recruiter, company)
    company.verification_status = CompanyVerificationStatus.VERIFIED.value
    company.recruiter_verification_status = RecruiterVerificationStatus.VERIFIED.value
    company.verification_note = payload.admin_note
    company.verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
    company.verified_by_admin_id = current_user.id
    membership.verification_status = RecruiterVerificationStatus.VERIFIED.value
    membership.company_join_status = CompanyJoinStatus.APPROVED.value
    membership.verified_at = company.verified_at
    membership.verified_by_admin_id = current_user.id
    membership.approved_by_admin_id = current_user.id
    membership.approved_at = company.verified_at
    membership.admin_note = payload.admin_note
    create_notification(
        db,
        recruiter_id,
        "Recruiter verified",
        "Your company profile has been verified. You can now post active jobs.",
        "RECRUITER_VERIFIED",
        "/recruiter/dashboard",
    )
    log_action(db, current_user, "VERIFY_RECRUITER", "USER", recruiter_id, payload.admin_note)
    db.commit()
    db.refresh(company)
    return recruiter_verification_response(company)


@router.put("/recruiters/{recruiter_id}/reject", response_model=AdminRecruiterVerificationRead)
def reject_recruiter(
    recruiter_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminRecruiterVerificationRead:
    company = db.scalar(
        select(CompanyProfile)
        .options(joinedload(CompanyProfile.recruiter), selectinload(CompanyProfile.members))
        .where(CompanyProfile.recruiter_id == recruiter_id)
    )
    if company is None or company.recruiter.role != UserRole.RECRUITER.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")

    membership = get_or_create_recruiter_membership(db, company.recruiter, company)
    company.verification_status = CompanyVerificationStatus.REJECTED.value
    company.recruiter_verification_status = RecruiterVerificationStatus.REJECTED.value
    company.verification_note = payload.admin_note
    company.verified_at = None
    company.verified_by_admin_id = current_user.id
    membership.verification_status = RecruiterVerificationStatus.REJECTED.value
    membership.company_join_status = CompanyJoinStatus.REJECTED.value
    membership.verified_at = None
    membership.verified_by_admin_id = current_user.id
    membership.admin_note = payload.admin_note
    create_notification(
        db,
        recruiter_id,
        "Recruiter verification rejected",
        f"Your company profile verification was rejected: {payload.admin_note}",
        "RECRUITER_REJECTED",
        "/recruiter/company",
    )
    log_action(db, current_user, "REJECT_RECRUITER", "USER", recruiter_id, payload.admin_note)
    db.commit()
    db.refresh(company)
    return recruiter_verification_response(company)


@router.get("/company-verifications", response_model=list[AdminRecruiterVerificationRead])
def company_verifications(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AdminRecruiterVerificationRead]:
    companies = db.scalars(
        select(CompanyProfile)
        .options(joinedload(CompanyProfile.recruiter), selectinload(CompanyProfile.members))
        .order_by(CompanyProfile.verification_status.asc(), CompanyProfile.updated_at.desc())
    ).all()
    return [recruiter_verification_response(company) for company in companies if company.recruiter]


@router.put("/companies/{company_id}/verify", response_model=AdminRecruiterVerificationRead)
def verify_company(
    company_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminRecruiterVerificationRead:
    company = db.scalar(
        select(CompanyProfile)
        .options(joinedload(CompanyProfile.recruiter), selectinload(CompanyProfile.members))
        .where(CompanyProfile.id == company_id)
    )
    if company is None or company.recruiter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company.verification_status = CompanyVerificationStatus.VERIFIED.value
    company.recruiter_verification_status = RecruiterVerificationStatus.VERIFIED.value
    company.verification_note = payload.admin_note
    company.verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
    company.verified_by_admin_id = current_user.id
    membership = get_or_create_recruiter_membership(db, company.recruiter, company)
    membership.verification_status = RecruiterVerificationStatus.VERIFIED.value
    membership.company_join_status = CompanyJoinStatus.APPROVED.value
    membership.verified_at = company.verified_at
    membership.verified_by_admin_id = current_user.id
    membership.approved_by_admin_id = current_user.id
    membership.approved_at = company.verified_at
    membership.admin_note = payload.admin_note
    log_action(db, current_user, "VERIFY_COMPANY", "COMPANY", company.id, payload.admin_note)
    db.commit()
    db.refresh(company)
    return recruiter_verification_response(company)


@router.put("/companies/{company_id}/reject", response_model=AdminRecruiterVerificationRead)
def reject_company(
    company_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminRecruiterVerificationRead:
    company = db.scalar(
        select(CompanyProfile)
        .options(joinedload(CompanyProfile.recruiter), selectinload(CompanyProfile.members))
        .where(CompanyProfile.id == company_id)
    )
    if company is None or company.recruiter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company.verification_status = CompanyVerificationStatus.REJECTED.value
    company.recruiter_verification_status = RecruiterVerificationStatus.REJECTED.value
    company.verification_note = payload.admin_note
    company.verified_at = None
    company.verified_by_admin_id = current_user.id
    for membership in company.members:
        membership.verification_status = RecruiterVerificationStatus.REJECTED.value
        membership.company_join_status = CompanyJoinStatus.REJECTED.value
        membership.verified_at = None
        membership.verified_by_admin_id = current_user.id
        membership.admin_note = payload.admin_note
    log_action(db, current_user, "REJECT_COMPANY", "COMPANY", company.id, payload.admin_note)
    db.commit()
    db.refresh(company)
    return recruiter_verification_response(company)


@router.put("/companies/{company_id}/suspend", response_model=AdminRecruiterVerificationRead)
def suspend_company(
    company_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminRecruiterVerificationRead:
    company = db.scalar(
        select(CompanyProfile)
        .options(joinedload(CompanyProfile.recruiter), selectinload(CompanyProfile.members))
        .where(CompanyProfile.id == company_id)
    )
    if company is None or company.recruiter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company.verification_status = CompanyVerificationStatus.SUSPENDED.value
    company.recruiter_verification_status = RecruiterVerificationStatus.SUSPENDED.value
    company.verification_note = payload.admin_note
    for membership in company.members:
        membership.verification_status = RecruiterVerificationStatus.SUSPENDED.value
        membership.admin_note = payload.admin_note
    for job in db.scalars(select(Job).where(Job.company_id == company.id)).all():
        job.moderation_status = JobModerationStatus.PAUSED.value
        job.moderation_reason = "Company suspended by admin."
    log_action(db, current_user, "SUSPEND_COMPANY", "COMPANY", company.id, payload.admin_note)
    db.commit()
    db.refresh(company)
    return recruiter_verification_response(company)


@router.get("/recruiter-memberships", response_model=list[RecruiterCompanyMemberRead])
def recruiter_memberships(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[RecruiterCompanyMemberRead]:
    members = db.scalars(
        select(RecruiterCompanyMember)
        .options(joinedload(RecruiterCompanyMember.recruiter), joinedload(RecruiterCompanyMember.company))
        .order_by(RecruiterCompanyMember.verification_status.asc(), RecruiterCompanyMember.updated_at.desc())
    ).all()
    return [membership_response(member) for member in members]


@router.put("/recruiter-memberships/{membership_id}/verify", response_model=RecruiterCompanyMemberRead)
def verify_recruiter_membership(
    membership_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> RecruiterCompanyMemberRead:
    member = db.scalar(
        select(RecruiterCompanyMember)
        .options(joinedload(RecruiterCompanyMember.recruiter), joinedload(RecruiterCompanyMember.company))
        .where(RecruiterCompanyMember.id == membership_id)
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter membership not found")
    if member.company.verification_status != CompanyVerificationStatus.VERIFIED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company must be verified before recruiter membership can be verified.")
    member.verification_status = RecruiterVerificationStatus.VERIFIED.value
    member.company_join_status = CompanyJoinStatus.APPROVED.value
    member.verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
    member.verified_by_admin_id = current_user.id
    member.approved_by_admin_id = current_user.id
    member.approved_at = member.verified_at
    member.admin_note = payload.admin_note
    member.company.recruiter_verification_status = RecruiterVerificationStatus.VERIFIED.value
    log_action(db, current_user, "VERIFY_RECRUITER_MEMBERSHIP", "RECRUITER_COMPANY_MEMBER", member.id, payload.admin_note)
    db.commit()
    db.refresh(member)
    return membership_response(member)


@router.put("/recruiter-memberships/{membership_id}/reject", response_model=RecruiterCompanyMemberRead)
def reject_recruiter_membership(
    membership_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> RecruiterCompanyMemberRead:
    member = db.scalar(
        select(RecruiterCompanyMember)
        .options(joinedload(RecruiterCompanyMember.recruiter), joinedload(RecruiterCompanyMember.company))
        .where(RecruiterCompanyMember.id == membership_id)
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter membership not found")
    member.verification_status = RecruiterVerificationStatus.REJECTED.value
    member.company_join_status = CompanyJoinStatus.REJECTED.value
    member.verified_at = None
    member.verified_by_admin_id = current_user.id
    member.admin_note = payload.admin_note
    log_action(db, current_user, "REJECT_RECRUITER_MEMBERSHIP", "RECRUITER_COMPANY_MEMBER", member.id, payload.admin_note)
    db.commit()
    db.refresh(member)
    return membership_response(member)


@router.put("/recruiter-memberships/{membership_id}/suspend", response_model=RecruiterCompanyMemberRead)
def suspend_recruiter_membership(
    membership_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> RecruiterCompanyMemberRead:
    member = db.scalar(
        select(RecruiterCompanyMember)
        .options(joinedload(RecruiterCompanyMember.recruiter), joinedload(RecruiterCompanyMember.company))
        .where(RecruiterCompanyMember.id == membership_id)
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter membership not found")
    member.verification_status = RecruiterVerificationStatus.SUSPENDED.value
    member.admin_note = payload.admin_note
    for job in db.scalars(select(Job).where(Job.recruiter_id == member.recruiter_id).where(Job.company_id == member.company_id)).all():
        job.moderation_status = JobModerationStatus.PAUSED.value
        job.moderation_reason = "Recruiter membership suspended by admin."
    log_action(db, current_user, "SUSPEND_RECRUITER_MEMBERSHIP", "RECRUITER_COMPANY_MEMBER", member.id, payload.admin_note)
    db.commit()
    db.refresh(member)
    return membership_response(member)


@router.get("/suspicious-jobs", response_model=list[JobRead])
def suspicious_jobs(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Job]:
    jobs = db.scalars(select(Job).where(Job.risk_score > 0).order_by(Job.updated_at.desc())).all()
    return [attach_job_trust(db, job) for job in jobs]


@router.get("/company-reviews", response_model=list[CompanyReviewRead])
def company_reviews(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[CompanyReviewRead]:
    reviews = db.scalars(
        select(CompanyReview)
        .options(joinedload(CompanyReview.reviewer))
        .order_by(CompanyReview.created_at.desc(), CompanyReview.id.desc())
    ).all()
    return [review_response(review) for review in reviews]


@router.put("/company-reviews/{review_id}/moderate", response_model=CompanyReviewRead)
def moderate_company_review(
    review_id: int,
    payload: CompanyReviewModerationRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyReviewRead:
    review = db.scalar(
        select(CompanyReview).options(joinedload(CompanyReview.reviewer)).where(CompanyReview.id == review_id)
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company review not found")
    review.moderation_status = payload.moderation_status.value
    review.is_visible = payload.moderation_status == ReviewModerationStatus.VISIBLE
    review.is_flagged = payload.moderation_status == ReviewModerationStatus.FLAGGED
    log_action(db, current_user, f"REVIEW_{payload.moderation_status.value}", "COMPANY_REVIEW", review.id, payload.admin_note)
    db.commit()
    db.refresh(review)
    return review_response(review)


def user_document_response(document: UserDocument) -> AdminUserDocumentRead:
    return AdminUserDocumentRead(
        id=document.id,
        owner_user_id=document.owner_user_id,
        owner_name=document.owner.name if document.owner else None,
        owner_email=document.owner.email if document.owner else None,
        owner_role=document.owner.role if document.owner else None,
        document_type=document.document_type,
        original_filename=document.original_filename,
        is_public=document.is_public,
        verification_status=document.verification_status,
        reviewed_by=document.reviewed_by,
        reviewed_at=document.reviewed_at,
        review_note=document.review_note,
        file_url=document.file_url,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get("/jobseeker-verifications", response_model=list[UserRead])
def jobseeker_verifications(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .join(JobSeekerProfile, JobSeekerProfile.user_id == User.id)
            .where(User.role == UserRole.JOB_SEEKER.value)
            .where(JobSeekerProfile.verification_status == JobSeekerVerificationStatus.PENDING.value)
            .order_by(User.updated_at.desc())
        ).all()
    )


def set_jobseeker_verification(
    user_id: int,
    status_value: JobSeekerVerificationStatus,
    payload: AdminNoteRequest,
    current_user: User,
    db: Session,
) -> User:
    user = db.scalar(
        select(User)
        .options(joinedload(User.job_seeker_profile))
        .where(User.id == user_id)
        .where(User.role == UserRole.JOB_SEEKER.value)
    )
    if user is None or user.job_seeker_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job seeker not found")
    user.job_seeker_profile.verification_status = status_value.value
    log_action(db, current_user, f"JOBSEEKER_{status_value.value}", "USER", user.id, payload.admin_note)
    db.commit()
    db.refresh(user)
    return user


@router.put("/jobseekers/{user_id}/verify", response_model=UserRead)
def verify_jobseeker(
    user_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    return set_jobseeker_verification(user_id, JobSeekerVerificationStatus.VERIFIED, payload, current_user, db)


@router.put("/jobseekers/{user_id}/reject", response_model=UserRead)
def reject_jobseeker(
    user_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    return set_jobseeker_verification(user_id, JobSeekerVerificationStatus.REJECTED, payload, current_user, db)


@router.put("/jobseekers/{user_id}/suspend", response_model=UserRead)
def suspend_jobseeker_verification(
    user_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    return set_jobseeker_verification(user_id, JobSeekerVerificationStatus.SUSPENDED, payload, current_user, db)


@router.get("/user-documents", response_model=list[AdminUserDocumentRead])
def user_documents(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AdminUserDocumentRead]:
    documents = db.scalars(
        select(UserDocument)
        .options(joinedload(UserDocument.owner))
        .order_by(UserDocument.verification_status.asc(), UserDocument.created_at.desc())
    ).all()
    return [user_document_response(document) for document in documents]


@router.put("/user-documents/{document_id}/review", response_model=AdminUserDocumentRead)
def review_user_document(
    document_id: int,
    payload: DocumentReviewRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminUserDocumentRead:
    document = db.scalar(
        select(UserDocument).options(joinedload(UserDocument.owner)).where(UserDocument.id == document_id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if payload.verification_status not in {
        DocumentVerificationStatus.PENDING,
        DocumentVerificationStatus.VERIFIED,
        DocumentVerificationStatus.REJECTED,
    }:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported document status")
    document.verification_status = payload.verification_status.value
    document.review_note = payload.review_note
    document.reviewed_by = current_user.id
    document.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    log_action(db, current_user, f"DOCUMENT_{payload.verification_status.value}", "USER_DOCUMENT", document.id, payload.review_note)
    db.commit()
    db.refresh(document)
    return user_document_response(document)


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
        accepted_privacy=True,
        accepted_privacy_at=datetime.now(timezone.utc).replace(tzinfo=None),
        email_verified=True,
        email_verified_at=datetime.now(timezone.utc).replace(tzinfo=None),
        account_status=AccountStatus.ACTIVE.value,
        is_protected_owner=False,
    )
    db.add(user)
    db.flush()
    ensure_user_public_identity(db, user)
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
