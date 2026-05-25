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
from app.models.company_claim_request import CompanyClaimRequest
from app.models.company_member import CompanyMember
from app.models.company_review import CompanyReview
from app.models.candidate_risk_assessment import CandidateRiskAssessment
from app.models.enums import (
    AccountStatus,
    ApplicationAdminStatus,
    ChatThreadStatus,
    CompanyClaimStatus,
    CompanyMemberRole,
    CompanyVerificationStatus,
    JobModerationStatus,
    RecruiterVerificationStatus,
    ReportStatus,
    ReviewModerationStatus,
    RiskAutoAction,
    UserRole,
)
from app.models.job import Job
from app.models.job_risk_assessment import JobRiskAssessment
from app.models.recruiter_profile import RecruiterProfile
from app.models.recruiter_review import RecruiterReview
from app.models.report import Report
from app.models.swipe import Swipe
from app.models.user import User
from app.models.user_risk_assessment import UserRiskAssessment
from app.schemas.admin import (
    AdminActionLogRead,
    AdminCreateRequest,
    AdminNoteRequest,
    AdminReasonRequest,
    CandidateRiskAssessmentRead,
    JobRiskAssessmentRead,
    UserRiskAssessmentRead,
)
from app.schemas.application import ApplicationRead
from app.schemas.chat import ChatThreadRead
from app.schemas.auth import UserRead
from app.schemas.company import AdminCompanyReviewRead, CompanyClaimRead, CompanyJoinRequestRead, CompanyRead
from app.schemas.job import JobRead
from app.schemas.profile import AdminRecruiterVerificationRead
from app.schemas.report import ReportRead, ReportStatusUpdate
from app.schemas.review import RecruiterReviewRead, ReviewAnalyticsRead
from app.schemas.security import SecuritySettingsRead, SecuritySettingsUpdate
from app.schemas.swipe import SwipeRead
from app.services.company_reviews import recalculate_company_rating
from app.services.company_claims import ensure_company_member, finalize_claim_as_verified, reject_company_member
from app.services.captcha import get_security_settings
from app.services.notifications import create_notification
from app.services.recruiter_reviews import recalculate_recruiter_rating
from app.services.timeline import add_timeline_event
from app.services.user_risk_assessment import update_user_risk
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


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_user_exists(user: User | None) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def admin_company_claim_response(claim: CompanyClaimRequest) -> CompanyClaimRead:
    return CompanyClaimRead(
        id=claim.id,
        company_id=claim.company_id,
        requested_company_name=claim.requested_company_name,
        requested_domain=claim.requested_domain,
        requester_user_id=claim.requester_user_id,
        official_email=claim.official_email,
        claim_status=claim.claim_status,
        email_verified_at=claim.email_verified_at,
        reviewed_by_admin_id=claim.reviewed_by_admin_id,
        admin_note=claim.admin_note,
        risk_score=claim.risk_score,
        risk_level=claim.risk_level,
        requires_admin_review=claim.requires_admin_review,
        risk_reasons=claim.risk_reasons,
        company_name=claim.company.company_name if claim.company else None,
        requester_name=claim.requester.name if claim.requester else None,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
    )


def admin_company_member_response(member: CompanyMember) -> CompanyJoinRequestRead:
    return CompanyJoinRequestRead(
        id=member.id,
        company_id=member.company_id,
        user_id=member.user_id,
        company_role=member.company_role,
        verification_status=member.verification_status,
        requested_at=member.requested_at,
        verified_at=member.verified_at,
        verified_by_user_id=member.verified_by_user_id,
        note=member.note,
        user_name=member.user.name if member.user else None,
        user_email=member.user.email if member.user else None,
        company_name=member.company.company_name if member.company else None,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def job_risk_response(assessment: JobRiskAssessment) -> JobRiskAssessmentRead:
    job = assessment.job
    recruiter = job.recruiter if job else None
    return JobRiskAssessmentRead(
        id=assessment.id,
        job_id=assessment.job_id,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        reasons=assessment.reasons,
        auto_action=assessment.auto_action,
        reviewed_by_admin_id=assessment.reviewed_by_admin_id,
        reviewed_at=assessment.reviewed_at,
        job_title=job.title if job else None,
        company_name=job.company_name if job else None,
        recruiter_id=job.recruiter_id if job else None,
        recruiter_name=recruiter.name if recruiter else None,
        moderation_status=job.moderation_status if job else None,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
    )


def candidate_risk_response(assessment: CandidateRiskAssessment) -> CandidateRiskAssessmentRead:
    user = assessment.job_seeker
    return CandidateRiskAssessmentRead(
        id=assessment.id,
        job_seeker_id=assessment.job_seeker_id,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        reasons=assessment.reasons,
        reviewed_by_admin_id=assessment.reviewed_by_admin_id,
        reviewed_at=assessment.reviewed_at,
        admin_note=assessment.admin_note,
        job_seeker_name=user.name if user else None,
        job_seeker_email=user.email if user else None,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
    )


def user_risk_response(assessment: UserRiskAssessment) -> UserRiskAssessmentRead:
    user = assessment.user
    return UserRiskAssessmentRead(
        id=assessment.id,
        user_id=assessment.user_id,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        reasons=assessment.reasons,
        last_evaluated_at=assessment.last_evaluated_at,
        reviewed_by_admin_id=assessment.reviewed_by_admin_id,
        reviewed_at=assessment.reviewed_at,
        admin_note=assessment.admin_note,
        user_name=user.name if user else None,
        user_email=user.email if user else None,
        user_role=user.role if user else None,
        account_status=user.account_status if user else None,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
    )


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


@router.get("/security-settings", response_model=SecuritySettingsRead)
def security_settings(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> SecuritySettingsRead:
    return get_security_settings(db)


@router.put("/security-settings", response_model=SecuritySettingsRead)
def update_security_settings(
    payload: SecuritySettingsUpdate,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> SecuritySettingsRead:
    settings = get_security_settings(db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    log_action(db, current_user, "UPDATE_SECURITY_SETTINGS", "SECURITY_SETTINGS", settings.id)
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/company-claims", response_model=list[CompanyClaimRead])
def company_claims(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[CompanyClaimRead]:
    statement = (
        select(CompanyClaimRequest)
        .options(joinedload(CompanyClaimRequest.company), joinedload(CompanyClaimRequest.requester))
        .order_by(CompanyClaimRequest.requires_admin_review.desc(), CompanyClaimRequest.created_at.desc())
    )
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                CompanyClaimRequest.requested_company_name.ilike(term),
                CompanyClaimRequest.requested_domain.ilike(term),
                CompanyClaimRequest.official_email.ilike(term),
            )
        )
    claims = db.scalars(statement.offset(pagination_offset(page, limit)).limit(limit)).all()
    return [admin_company_claim_response(claim) for claim in claims]


@router.get("/company-members", response_model=list[CompanyJoinRequestRead])
def company_member_requests(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    verification_status: str | None = None,
    search: str | None = None,
) -> list[CompanyJoinRequestRead]:
    statement = (
        select(CompanyMember)
        .options(joinedload(CompanyMember.user), joinedload(CompanyMember.company))
        .order_by(CompanyMember.verification_status.asc(), CompanyMember.created_at.desc())
    )
    if verification_status:
        statement = statement.where(CompanyMember.verification_status == verification_status.upper())
    if search:
        term = f"%{search.strip()}%"
        statement = statement.join(User, CompanyMember.user_id == User.id).join(Company, CompanyMember.company_id == Company.id)
        statement = statement.where(or_(User.name.ilike(term), User.email.ilike(term), Company.company_name.ilike(term)))
    members = db.scalars(statement.offset(pagination_offset(page, limit)).limit(limit)).all()
    return [admin_company_member_response(member) for member in members]


@router.put("/company-claims/{claim_id}/approve", response_model=CompanyClaimRead)
def approve_company_claim(
    claim_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyClaimRead:
    claim = db.scalar(
        select(CompanyClaimRequest)
        .options(joinedload(CompanyClaimRequest.company), joinedload(CompanyClaimRequest.requester))
        .where(CompanyClaimRequest.id == claim_id)
    )
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company claim not found")
    if claim.email_verified_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Official email must be verified before approval.")
    claim.admin_note = payload.admin_note
    finalize_claim_as_verified(db, claim, current_user)
    log_action(db, current_user, "APPROVE_COMPANY_CLAIM", "COMPANY_CLAIM", claim.id, payload.admin_note)
    db.commit()
    db.refresh(claim)
    return admin_company_claim_response(claim)


@router.put("/company-claims/{claim_id}/reject", response_model=CompanyClaimRead)
def reject_company_claim(
    claim_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> CompanyClaimRead:
    claim = db.scalar(
        select(CompanyClaimRequest)
        .options(joinedload(CompanyClaimRequest.company), joinedload(CompanyClaimRequest.requester))
        .where(CompanyClaimRequest.id == claim_id)
    )
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company claim not found")
    claim.claim_status = CompanyClaimStatus.REJECTED.value
    claim.reviewed_by_admin_id = current_user.id
    claim.admin_note = payload.admin_note
    if claim.company:
        claim.company.verification_status = CompanyVerificationStatus.REJECTED.value
        claim.company.verification_note = payload.admin_note
    member = db.scalar(
        select(CompanyMember)
        .where(CompanyMember.company_id == claim.company_id)
        .where(CompanyMember.user_id == claim.requester_user_id)
    )
    if member:
        reject_company_member(db, member, current_user, payload.admin_note)
    create_notification(
        db,
        claim.requester_user_id,
        "Company claim rejected",
        payload.admin_note,
        "COMPANY_CLAIM_REJECTED",
        "/recruiter/company",
    )
    log_action(db, current_user, "REJECT_COMPANY_CLAIM", "COMPANY_CLAIM", claim.id, payload.admin_note)
    requester = db.get(User, claim.requester_user_id)
    if requester:
        update_user_risk(db, requester)
    db.commit()
    db.refresh(claim)
    return admin_company_claim_response(claim)


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
    if profile.company_id:
        member = ensure_company_member(
            db,
            profile.company_id,
            profile.user_id,
            CompanyMemberRole.COMPANY_RECRUITER.value,
            RecruiterVerificationStatus.VERIFIED.value,
            payload.admin_note,
        )
        member.verified_at = profile.verified_at
        member.verified_by_user_id = current_user.id
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
    if profile.company_id:
        member = db.scalar(
            select(CompanyMember)
            .where(CompanyMember.company_id == profile.company_id)
            .where(CompanyMember.user_id == profile.user_id)
        )
        if member:
            member.verification_status = RecruiterVerificationStatus.REJECTED.value
            member.note = payload.admin_note
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
        application_id=review.application_id,
        rating=review.rating,
        overall_rating=review.overall_rating,
        work_culture_rating=review.work_culture_rating,
        interview_process_rating=review.interview_process_rating,
        salary_transparency_rating=review.salary_transparency_rating,
        growth_opportunity_rating=review.growth_opportunity_rating,
        review_title=review.review_title,
        review_text=review.review_text,
        pros=review.pros,
        cons=review.cons,
        is_anonymous=review.is_anonymous,
        is_visible=review.is_visible,
        moderation_status=review.moderation_status,
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


def load_company_review(db: Session, review_id: int) -> CompanyReview:
    review = db.scalar(
        select(CompanyReview)
        .options(joinedload(CompanyReview.company), joinedload(CompanyReview.job_seeker))
        .where(CompanyReview.id == review_id)
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.put("/company-reviews/{review_id}/hide", response_model=AdminCompanyReviewRead)
def hide_company_review(
    review_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminCompanyReviewRead:
    review = load_company_review(db, review_id)
    review.is_visible = False
    review.moderation_status = ReviewModerationStatus.HIDDEN.value
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
    review = load_company_review(db, review_id)
    review.is_visible = True
    review.moderation_status = ReviewModerationStatus.VISIBLE.value
    recalculate_company_rating(db, review.company_id)
    log_action(db, current_user, "SHOW_COMPANY_REVIEW", "COMPANY_REVIEW", review.id)
    db.commit()
    db.refresh(review)
    return company_review_response(review)


@router.put("/company-reviews/{review_id}/flag", response_model=AdminCompanyReviewRead)
def flag_company_review(
    review_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminCompanyReviewRead:
    review = load_company_review(db, review_id)
    review.is_visible = False
    review.moderation_status = ReviewModerationStatus.FLAGGED.value
    recalculate_company_rating(db, review.company_id)
    log_action(db, current_user, "FLAG_COMPANY_REVIEW", "COMPANY_REVIEW", review.id)
    db.commit()
    db.refresh(review)
    return company_review_response(review)


def recruiter_review_response(review: RecruiterReview) -> RecruiterReviewRead:
    profile = review.recruiter.recruiter_profile if review.recruiter else None
    company = profile.company if profile else None
    return RecruiterReviewRead(
        id=review.id,
        recruiter_id=review.recruiter_id,
        job_seeker_id=review.job_seeker_id,
        application_id=review.application_id,
        overall_rating=review.overall_rating,
        communication_rating=review.communication_rating,
        response_time_rating=review.response_time_rating,
        professionalism_rating=review.professionalism_rating,
        transparency_rating=review.transparency_rating,
        review_title=review.review_title,
        review_text=review.review_text,
        is_anonymous=review.is_anonymous,
        is_visible=review.is_visible,
        moderation_status=review.moderation_status,
        reviewer_name=review.job_seeker.name if review.job_seeker else None,
        recruiter_name=review.recruiter.name if review.recruiter else None,
        recruiter_email=review.recruiter.email if review.recruiter else None,
        company_name=company.company_name if company else None,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.get("/recruiter-reviews", response_model=list[RecruiterReviewRead])
def recruiter_reviews(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    search: str | None = None,
) -> list[RecruiterReviewRead]:
    statement = (
        select(RecruiterReview)
        .join(User, RecruiterReview.recruiter_id == User.id)
        .options(
            joinedload(RecruiterReview.job_seeker),
            joinedload(RecruiterReview.recruiter).joinedload(User.recruiter_profile).joinedload(RecruiterProfile.company),
        )
        .order_by(RecruiterReview.created_at.desc(), RecruiterReview.id.desc())
    )
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(User.name.ilike(term), User.email.ilike(term), RecruiterReview.review_text.ilike(term)))
    rows = db.scalars(statement.offset(pagination_offset(page, limit)).limit(limit)).all()
    return [recruiter_review_response(row) for row in rows]


def load_recruiter_review(db: Session, review_id: int) -> RecruiterReview:
    review = db.scalar(
        select(RecruiterReview)
        .options(
            joinedload(RecruiterReview.job_seeker),
            joinedload(RecruiterReview.recruiter).joinedload(User.recruiter_profile).joinedload(RecruiterProfile.company),
        )
        .where(RecruiterReview.id == review_id)
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter review not found")
    return review


@router.put("/recruiter-reviews/{review_id}/hide", response_model=RecruiterReviewRead)
def hide_recruiter_review(
    review_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> RecruiterReviewRead:
    review = load_recruiter_review(db, review_id)
    review.is_visible = False
    review.moderation_status = ReviewModerationStatus.HIDDEN.value
    recalculate_recruiter_rating(db, review.recruiter_id)
    log_action(db, current_user, "HIDE_RECRUITER_REVIEW", "RECRUITER_REVIEW", review.id)
    db.commit()
    db.refresh(review)
    return recruiter_review_response(review)


@router.put("/recruiter-reviews/{review_id}/show", response_model=RecruiterReviewRead)
def show_recruiter_review(
    review_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> RecruiterReviewRead:
    review = load_recruiter_review(db, review_id)
    review.is_visible = True
    review.moderation_status = ReviewModerationStatus.VISIBLE.value
    recalculate_recruiter_rating(db, review.recruiter_id)
    log_action(db, current_user, "SHOW_RECRUITER_REVIEW", "RECRUITER_REVIEW", review.id)
    db.commit()
    db.refresh(review)
    return recruiter_review_response(review)


@router.put("/recruiter-reviews/{review_id}/flag", response_model=RecruiterReviewRead)
def flag_recruiter_review(
    review_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> RecruiterReviewRead:
    review = load_recruiter_review(db, review_id)
    review.is_visible = False
    review.moderation_status = ReviewModerationStatus.FLAGGED.value
    recalculate_recruiter_rating(db, review.recruiter_id)
    log_action(db, current_user, "FLAG_RECRUITER_REVIEW", "RECRUITER_REVIEW", review.id)
    db.commit()
    db.refresh(review)
    return recruiter_review_response(review)


@router.get("/analytics/reviews", response_model=ReviewAnalyticsRead)
def review_analytics(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> ReviewAnalyticsRead:
    highest_companies = db.scalars(
        select(Company).where(Company.total_reviews > 0).order_by(Company.average_rating.desc(), Company.total_reviews.desc()).limit(5)
    ).all()
    lowest_companies = db.scalars(
        select(Company).where(Company.total_reviews > 0).order_by(Company.average_rating.asc(), Company.total_reviews.desc()).limit(5)
    ).all()
    most_reviewed = db.scalars(
        select(Company).where(Company.total_reviews > 0).order_by(Company.total_reviews.desc(), Company.average_rating.desc()).limit(5)
    ).all()
    low_recruiters = db.scalars(
        select(RecruiterProfile)
        .options(joinedload(RecruiterProfile.recruiter), joinedload(RecruiterProfile.company))
        .where(RecruiterProfile.total_reviews > 0)
        .order_by(RecruiterProfile.average_rating.asc(), RecruiterProfile.total_reviews.desc())
        .limit(5)
    ).all()
    recent_company_reviews = db.scalars(
        select(CompanyReview)
        .options(joinedload(CompanyReview.company), joinedload(CompanyReview.job_seeker))
        .order_by(CompanyReview.created_at.desc(), CompanyReview.id.desc())
        .limit(5)
    ).all()
    recent_recruiter_reviews = db.scalars(
        select(RecruiterReview)
        .options(
            joinedload(RecruiterReview.job_seeker),
            joinedload(RecruiterReview.recruiter).joinedload(User.recruiter_profile).joinedload(RecruiterProfile.company),
        )
        .order_by(RecruiterReview.created_at.desc(), RecruiterReview.id.desc())
        .limit(5)
    ).all()
    hidden_reviews_count = (db.scalar(select(func.count(CompanyReview.id)).where(CompanyReview.moderation_status == ReviewModerationStatus.HIDDEN.value)) or 0) + (
        db.scalar(select(func.count(RecruiterReview.id)).where(RecruiterReview.moderation_status == ReviewModerationStatus.HIDDEN.value)) or 0
    )
    flagged_reviews_count = (db.scalar(select(func.count(CompanyReview.id)).where(CompanyReview.moderation_status == ReviewModerationStatus.FLAGGED.value)) or 0) + (
        db.scalar(select(func.count(RecruiterReview.id)).where(RecruiterReview.moderation_status == ReviewModerationStatus.FLAGGED.value)) or 0
    )
    return ReviewAnalyticsRead(
        highest_rated_companies=[
            {"id": company.id, "name": company.company_name, "average_rating": company.average_rating, "total_reviews": company.total_reviews}
            for company in highest_companies
        ],
        lowest_rated_companies=[
            {"id": company.id, "name": company.company_name, "average_rating": company.average_rating, "total_reviews": company.total_reviews}
            for company in lowest_companies
        ],
        most_reviewed_companies=[
            {"id": company.id, "name": company.company_name, "average_rating": company.average_rating, "total_reviews": company.total_reviews}
            for company in most_reviewed
        ],
        low_rated_recruiters=[
            {
                "id": profile.user_id,
                "name": profile.recruiter.name if profile.recruiter else "Recruiter",
                "company_name": profile.company.company_name if profile.company else None,
                "average_rating": profile.average_rating,
                "total_reviews": profile.total_reviews,
            }
            for profile in low_recruiters
        ],
        recent_company_reviews=[company_review_response(review).model_dump(mode="json") for review in recent_company_reviews],
        recent_recruiter_reviews=[recruiter_review_response(review).model_dump(mode="json") for review in recent_recruiter_reviews],
        hidden_reviews_count=int(hidden_reviews_count),
        flagged_reviews_count=int(flagged_reviews_count),
    )


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


@router.get("/risk/jobs", response_model=list[JobRiskAssessmentRead])
def risky_jobs(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
) -> list[JobRiskAssessmentRead]:
    rows = db.scalars(
        select(JobRiskAssessment)
        .options(joinedload(JobRiskAssessment.job).joinedload(Job.recruiter))
        .where(JobRiskAssessment.risk_score >= 31)
        .order_by(JobRiskAssessment.risk_score.desc(), JobRiskAssessment.created_at.desc())
        .offset(pagination_offset(page, limit))
        .limit(limit)
    ).all()
    return [job_risk_response(row) for row in rows]


@router.put("/risk/jobs/{job_id}/approve", response_model=JobRiskAssessmentRead)
def approve_risky_job(
    job_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> JobRiskAssessmentRead:
    assessment = db.scalar(
        select(JobRiskAssessment)
        .options(joinedload(JobRiskAssessment.job).joinedload(Job.recruiter))
        .where(JobRiskAssessment.job_id == job_id)
    )
    if assessment is None or assessment.job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk assessment not found")
    assessment.job.moderation_status = JobModerationStatus.ACTIVE.value
    assessment.job.moderation_reason = None
    assessment.reviewed_by_admin_id = current_user.id
    assessment.reviewed_at = utc_now_naive()
    assessment.auto_action = RiskAutoAction.NONE.value
    log_action(db, current_user, "APPROVE_RISKY_JOB", "JOB", job_id)
    db.commit()
    db.refresh(assessment)
    return job_risk_response(assessment)


@router.put("/risk/jobs/{job_id}/pause", response_model=JobRiskAssessmentRead)
def pause_risky_job(
    job_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> JobRiskAssessmentRead:
    assessment = db.scalar(
        select(JobRiskAssessment)
        .options(joinedload(JobRiskAssessment.job).joinedload(Job.recruiter))
        .where(JobRiskAssessment.job_id == job_id)
    )
    if assessment is None or assessment.job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk assessment not found")
    assessment.job.moderation_status = JobModerationStatus.PAUSED.value
    assessment.job.moderation_reason = "Kept paused after safety review."
    assessment.reviewed_by_admin_id = current_user.id
    assessment.reviewed_at = utc_now_naive()
    log_action(db, current_user, "PAUSE_RISKY_JOB", "JOB", job_id)
    db.commit()
    db.refresh(assessment)
    return job_risk_response(assessment)


@router.put("/risk/jobs/{job_id}/remove", response_model=JobRiskAssessmentRead)
def remove_risky_job(
    job_id: int,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> JobRiskAssessmentRead:
    assessment = db.scalar(
        select(JobRiskAssessment)
        .options(joinedload(JobRiskAssessment.job).joinedload(Job.recruiter))
        .where(JobRiskAssessment.job_id == job_id)
    )
    if assessment is None or assessment.job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk assessment not found")
    assessment.job.moderation_status = JobModerationStatus.REMOVED.value
    assessment.job.moderation_reason = "Removed after safety review."
    assessment.reviewed_by_admin_id = current_user.id
    assessment.reviewed_at = utc_now_naive()
    log_action(db, current_user, "REMOVE_RISKY_JOB", "JOB", job_id)
    db.commit()
    db.refresh(assessment)
    return job_risk_response(assessment)


@router.get("/risk/candidates", response_model=list[CandidateRiskAssessmentRead])
def risky_candidates(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
) -> list[CandidateRiskAssessmentRead]:
    rows = db.scalars(
        select(CandidateRiskAssessment)
        .options(joinedload(CandidateRiskAssessment.job_seeker))
        .order_by(CandidateRiskAssessment.risk_score.desc(), CandidateRiskAssessment.created_at.desc())
        .offset(pagination_offset(page, limit))
        .limit(limit)
    ).all()
    return [candidate_risk_response(row) for row in rows]


@router.get("/risk/users", response_model=list[UserRiskAssessmentRead])
def risky_users(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    page: PageQuery = 1,
    limit: LimitQuery = 20,
) -> list[UserRiskAssessmentRead]:
    rows = db.scalars(
        select(UserRiskAssessment)
        .options(joinedload(UserRiskAssessment.user))
        .where(UserRiskAssessment.risk_score >= 31)
        .order_by(UserRiskAssessment.risk_score.desc(), UserRiskAssessment.updated_at.desc())
        .offset(pagination_offset(page, limit))
        .limit(limit)
    ).all()
    return [user_risk_response(row) for row in rows]


@router.get("/risk/users/{user_id}", response_model=UserRiskAssessmentRead)
def user_risk_detail(
    user_id: int,
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> UserRiskAssessmentRead:
    user = ensure_user_exists(db.get(User, user_id))
    assessment = update_user_risk(db, user)
    db.commit()
    db.refresh(assessment)
    return user_risk_response(assessment)


@router.put("/risk/users/{user_id}/review", response_model=UserRiskAssessmentRead)
def review_risky_user(
    user_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> UserRiskAssessmentRead:
    user = ensure_user_exists(db.get(User, user_id))
    assessment = update_user_risk(db, user)
    assessment.reviewed_by_admin_id = current_user.id
    assessment.reviewed_at = utc_now_naive()
    assessment.admin_note = payload.admin_note
    log_action(db, current_user, "REVIEW_USER_RISK", "USER", user.id, payload.admin_note)
    db.commit()
    db.refresh(assessment)
    return user_risk_response(assessment)


@router.put("/risk/users/{user_id}/suspend", response_model=UserRiskAssessmentRead)
def suspend_risky_user(
    user_id: int,
    payload: AdminReasonRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> UserRiskAssessmentRead:
    target = ensure_user_exists(db.get(User, user_id))
    ensure_moderation_target_allowed(current_user, target, "suspend")
    target.account_status = AccountStatus.SUSPENDED.value
    target.suspension_reason = payload.reason
    assessment = update_user_risk(db, target)
    assessment.reviewed_by_admin_id = current_user.id
    assessment.reviewed_at = utc_now_naive()
    assessment.admin_note = payload.reason
    create_notification(
        db,
        target.id,
        "Account suspended",
        payload.reason,
        "USER_SUSPENDED",
        "/login",
    )
    log_action(db, current_user, "SUSPEND_USER_RISK", "USER", target.id, payload.reason)
    db.commit()
    db.refresh(assessment)
    return user_risk_response(assessment)


@router.put("/risk/candidates/{assessment_id}/review", response_model=CandidateRiskAssessmentRead)
def review_risky_candidate(
    assessment_id: int,
    payload: AdminNoteRequest,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> CandidateRiskAssessmentRead:
    assessment = db.scalar(
        select(CandidateRiskAssessment)
        .options(joinedload(CandidateRiskAssessment.job_seeker))
        .where(CandidateRiskAssessment.id == assessment_id)
    )
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate risk assessment not found")
    assessment.reviewed_by_admin_id = current_user.id
    assessment.reviewed_at = utc_now_naive()
    assessment.admin_note = payload.admin_note
    log_action(db, current_user, "REVIEW_CANDIDATE_RISK", "CANDIDATE_RISK", assessment.id, payload.admin_note)
    db.commit()
    db.refresh(assessment)
    return candidate_risk_response(assessment)
