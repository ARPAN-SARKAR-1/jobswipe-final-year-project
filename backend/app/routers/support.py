import logging
from datetime import datetime, timezone
from html import escape
from secrets import choice
from string import ascii_uppercase, digits
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user, get_optional_current_user, require_admin_or_owner
from app.models.admin_action_log import AdminActionLog
from app.models.enums import SupportTicketPriority, SupportTicketStatus, UserRole
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.schemas.support import (
    SupportTicketAdminPage,
    SupportTicketAdminUpdate,
    SupportTicketCreate,
    SupportTicketListItem,
    SupportTicketResponse,
    SupportTicketSummary,
)
from app.services.email_service import send_email_message
from app.services.security_challenges import verify_captcha

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Support"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def generate_ticket_code(db: Session) -> str:
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    alphabet = ascii_uppercase + digits
    for _ in range(20):
        suffix = "".join(choice(alphabet) for _ in range(4))
        code = f"SFS-TKT-{date_part}-{suffix}"
        if db.scalar(select(SupportTicket.id).where(SupportTicket.ticket_code == code)) is None:
            return code
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate support ticket code")


def support_recipients() -> list[str]:
    recipients = [settings.support_email, settings.admin_contact_email]
    return list(dict.fromkeys(email.strip().lower() for email in recipients if email and email.strip()))


def ticket_text(ticket: SupportTicket) -> str:
    return "\n".join(
        [
            f"Ticket code: {ticket.ticket_code}",
            f"Subject: {ticket.subject}",
            f"Status: {ticket.status}",
            f"Created: {ticket.created_at}",
            "",
            "Our team will review this support request and follow up if more information is needed.",
        ]
    )


def admin_ticket_text(ticket: SupportTicket) -> str:
    return "\n".join(
        [
            f"Ticket code: {ticket.ticket_code}",
            f"Name: {ticket.name}",
            f"Email: {ticket.email}",
            f"Role: {ticket.role_type}",
            f"Category: {ticket.category}",
            f"Priority: {ticket.priority}",
            f"Subject: {ticket.subject}",
            f"Created: {ticket.created_at}",
            "",
            "Message:",
            ticket.message,
        ]
    )


def to_html(text: str) -> str:
    return "<br />".join(escape(line) for line in text.splitlines())


def send_ticket_notifications(ticket: SupportTicket) -> str | None:
    warning = None
    try:
        send_email_message(
            ticket.email,
            "Your Swipe for Success support ticket has been created",
            ticket_text(ticket),
            to_html(ticket_text(ticket)),
        )
    except Exception as exc:  # noqa: BLE001 - ticket creation must survive email provider outages.
        warning = "Ticket created, but email notification could not be sent. Please save your ticket code."
        logger.error(
            "Support ticket user email failed ticket=%s recipient_domain=%s error_class=%s error=%s",
            ticket.ticket_code,
            ticket.email.rsplit("@", 1)[-1].lower() if "@" in ticket.email else "unknown",
            exc.__class__.__name__,
            str(exc).splitlines()[0],
        )
    for recipient in support_recipients():
        try:
            send_email_message(
                recipient,
                f"New support ticket: {ticket.ticket_code}",
                admin_ticket_text(ticket),
                to_html(admin_ticket_text(ticket)),
            )
        except Exception as exc:  # noqa: BLE001 - admin email failure should not hide the ticket.
            warning = "Ticket created, but email notification could not be sent. Please save your ticket code."
            logger.error(
                "Support ticket admin email failed ticket=%s recipient_domain=%s error_class=%s error=%s",
                ticket.ticket_code,
                recipient.rsplit("@", 1)[-1].lower() if "@" in recipient else "unknown",
                exc.__class__.__name__,
                str(exc).splitlines()[0],
            )
    return warning


def ticket_response(ticket: SupportTicket, email_warning: str | None = None) -> SupportTicketResponse:
    data = SupportTicketResponse.model_validate(ticket).model_dump()
    data["email_warning"] = email_warning
    return SupportTicketResponse(**data)


def log_support_action(db: Session, admin: User, action_type: str, ticket_id: int, reason: str | None = None) -> None:
    db.add(
        AdminActionLog(
            admin_id=admin.id,
            action_type=action_type,
            target_type="SUPPORT_TICKET",
            target_id=ticket_id,
            reason=reason,
        )
    )


@router.post("/support/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    payload: SupportTicketCreate,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SupportTicketResponse:
    verify_captcha(db, "contact", payload.captcha_challenge_id, payload.captcha_answer)
    normalized_email = payload.email.lower()
    ticket = SupportTicket(
        ticket_code=generate_ticket_code(db),
        name=payload.name.strip(),
        email=normalized_email,
        role_type=payload.role_type.value,
        category=payload.category.value,
        priority=payload.priority.value,
        subject=payload.subject.strip(),
        message=payload.message.strip(),
        status=SupportTicketStatus.OPEN.value,
        user_id=current_user.id if current_user and current_user.email.lower() == normalized_email else None,
        source="AUTHENTICATED_USER" if current_user else "CONTACT_PAGE",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    email_warning = send_ticket_notifications(ticket)
    return ticket_response(ticket, email_warning)


@router.get("/support/my-tickets", response_model=list[SupportTicketListItem])
def my_support_tickets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[SupportTicket]:
    return list(
        db.scalars(
            select(SupportTicket)
            .where(or_(SupportTicket.user_id == current_user.id, func.lower(SupportTicket.email) == current_user.email.lower()))
            .order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
        ).all()
    )


@router.get("/admin/support-tickets/summary", response_model=SupportTicketSummary)
def support_ticket_summary(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> SupportTicketSummary:
    def count_status(value: SupportTicketStatus) -> int:
        return db.scalar(select(func.count(SupportTicket.id)).where(SupportTicket.status == value.value)) or 0

    return SupportTicketSummary(
        open=count_status(SupportTicketStatus.OPEN),
        in_progress=count_status(SupportTicketStatus.IN_PROGRESS),
        resolved=count_status(SupportTicketStatus.RESOLVED),
        closed=count_status(SupportTicketStatus.CLOSED),
    )


@router.get("/admin/support-tickets", response_model=SupportTicketAdminPage)
def admin_support_tickets(
    _current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(default=None, max_length=100),
    status_filter: str | None = Query(default=None, alias="status", max_length=30),
    priority: str | None = Query(default=None, max_length=20),
    category: str | None = Query(default=None, max_length=80),
    role_type: str | None = Query(default=None, max_length=40),
    sort_by: str = Query(default="created_at", max_length=30),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SupportTicketAdminPage:
    statement = select(SupportTicket)
    if q:
        pattern = f"%{q.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(SupportTicket.ticket_code).like(pattern),
                func.lower(SupportTicket.email).like(pattern),
                func.lower(SupportTicket.name).like(pattern),
                func.lower(SupportTicket.subject).like(pattern),
            )
        )
    if status_filter:
        statement = statement.where(SupportTicket.status == status_filter.strip().upper())
    if priority:
        statement = statement.where(SupportTicket.priority == priority.strip().upper())
    if category:
        statement = statement.where(SupportTicket.category == category.strip().upper())
    if role_type:
        statement = statement.where(SupportTicket.role_type == role_type.strip().upper())

    sort_columns = {
        "created_at": SupportTicket.created_at,
        "updated_at": SupportTicket.updated_at,
        "priority": SupportTicket.priority,
        "status": SupportTicket.status,
        "category": SupportTicket.category,
        "email": SupportTicket.email,
        "ticket_code": SupportTicket.ticket_code,
    }
    sort_column = sort_columns.get(sort_by, SupportTicket.created_at)
    order = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    tickets = list(db.scalars(statement.order_by(order, SupportTicket.id.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return SupportTicketAdminPage(
        items=[SupportTicketListItem.model_validate(ticket) for ticket in tickets],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.patch("/admin/support-tickets/{ticket_id}", response_model=SupportTicketListItem)
def update_support_ticket(
    ticket_id: int,
    payload: SupportTicketAdminUpdate,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> SupportTicket:
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    if payload.status:
        ticket.status = payload.status.value
        if payload.status == SupportTicketStatus.RESOLVED:
            ticket.resolved_at = utcnow()
        if payload.status == SupportTicketStatus.CLOSED:
            ticket.closed_at = utcnow()
    if payload.priority:
        ticket.priority = payload.priority.value
    if payload.assigned_admin_id is not None:
        assigned_admin = db.get(User, payload.assigned_admin_id)
        if assigned_admin is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned admin not found")
        if assigned_admin.role not in {UserRole.ADMIN.value, UserRole.OWNER.value}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Support tickets can only be assigned to Admin or Owner accounts")
        ticket.assigned_admin_id = assigned_admin.id
    if payload.admin_note is not None:
        ticket.admin_note = payload.admin_note
    log_support_action(db, current_user, "UPDATE_SUPPORT_TICKET", ticket.id, payload.admin_note)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/admin/support-tickets/{ticket_id}/resolve", response_model=SupportTicketListItem)
def resolve_support_ticket(
    ticket_id: int,
    payload: SupportTicketAdminUpdate,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> SupportTicket:
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    ticket.status = SupportTicketStatus.RESOLVED.value
    ticket.resolved_at = utcnow()
    if payload.admin_note is not None:
        ticket.admin_note = payload.admin_note
    log_support_action(db, current_user, "RESOLVE_SUPPORT_TICKET", ticket.id, payload.admin_note)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/admin/support-tickets/{ticket_id}/close", response_model=SupportTicketListItem)
def close_support_ticket(
    ticket_id: int,
    payload: SupportTicketAdminUpdate,
    current_user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> SupportTicket:
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    ticket.status = SupportTicketStatus.CLOSED.value
    ticket.closed_at = utcnow()
    if payload.admin_note is not None:
        ticket.admin_note = payload.admin_note
    log_support_action(db, current_user, "CLOSE_SUPPORT_TICKET", ticket.id, payload.admin_note)
    db.commit()
    db.refresh(ticket)
    return ticket
