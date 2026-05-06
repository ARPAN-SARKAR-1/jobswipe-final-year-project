from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.application import Application
from app.models.chat_message import ChatMessage
from app.models.chat_thread import ChatThread
from app.models.enums import (
    AccountStatus,
    ApplicationAdminStatus,
    ApplicationStatus,
    ChatThreadStatus,
    JobModerationStatus,
    UserRole,
)
from app.models.job import Job
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatMessageRead, ChatReadResponse, ChatStartRequest, ChatThreadRead
from app.services.notifications import create_notification
from app.services.timeline import add_timeline_event

router = APIRouter(prefix="/chats", tags=["Chats"])


def now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def serialize_thread(db: Session, thread: ChatThread, current_user: User | None = None) -> ChatThreadRead:
    unread_count = 0
    if current_user and current_user.id in {thread.recruiter_id, thread.job_seeker_id}:
        unread_count = (
            db.scalar(
                select(func.count(ChatMessage.id))
                .where(ChatMessage.thread_id == thread.id)
                .where(ChatMessage.sender_id != current_user.id)
                .where(ChatMessage.is_read.is_(False))
            )
            or 0
        )
    last_message = db.scalar(
        select(ChatMessage).where(ChatMessage.thread_id == thread.id).order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc()).limit(1)
    )
    return ChatThreadRead(
        id=thread.id,
        application_id=thread.application_id,
        recruiter_id=thread.recruiter_id,
        job_seeker_id=thread.job_seeker_id,
        job_id=thread.job_id,
        status=thread.status,
        started_by_recruiter=thread.started_by_recruiter,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        job_title=thread.job.title if thread.job else None,
        company_name=thread.job.company_name if thread.job else None,
        recruiter_name=thread.recruiter.name if thread.recruiter else None,
        job_seeker_name=thread.job_seeker.name if thread.job_seeker else None,
        application_status=thread.application.status if thread.application else None,
        unread_count=unread_count,
        last_message=last_message.message_text if last_message else None,
        last_message_at=last_message.created_at if last_message else None,
    )


def load_thread(db: Session, thread_id: int) -> ChatThread:
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
    return thread


def is_admin_or_owner(user: User) -> bool:
    return user.role in {UserRole.ADMIN.value, UserRole.OWNER.value}


def ensure_thread_reader(thread: ChatThread, current_user: User) -> None:
    if current_user.id in {thread.recruiter_id, thread.job_seeker_id} or is_admin_or_owner(current_user):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot access this chat")


def ensure_thread_sender(thread: ChatThread, current_user: User) -> None:
    if current_user.id not in {thread.recruiter_id, thread.job_seeker_id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only chat participants can send messages")
    if current_user.account_status == AccountStatus.SUSPENDED.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suspended users cannot send messages")
    if thread.status != ChatThreadStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This chat is not active")
    if not thread.started_by_recruiter:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recruiter must start the chat first")
    if thread.application.status != ApplicationStatus.SHORTLISTED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chat is only available for shortlisted applications")
    if thread.application.admin_status == ApplicationAdminStatus.PAUSED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This application is paused by admin")
    if thread.job.moderation_status != JobModerationStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This job is not available for chat")


@router.post("/start", response_model=ChatThreadRead, status_code=status.HTTP_201_CREATED)
def start_chat(
    payload: ChatStartRequest,
    current_user: Annotated[User, Depends(require_roles(UserRole.RECRUITER.value))],
    db: Annotated[Session, Depends(get_db)],
) -> ChatThreadRead:
    if current_user.account_status == AccountStatus.SUSPENDED.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suspended users cannot send messages")

    application = db.scalar(
        select(Application)
        .join(Job)
        .options(
            joinedload(Application.job),
            joinedload(Application.job_seeker),
            joinedload(Application.chat_thread),
        )
        .where(Application.id == payload.application_id)
        .where(Job.recruiter_id == current_user.id)
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application.status != ApplicationStatus.SHORTLISTED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chat can only be started for shortlisted applications")
    if application.admin_status == ApplicationAdminStatus.PAUSED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This application is paused by admin")
    if application.job.moderation_status != JobModerationStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This job is not available for chat")
    if application.chat_thread:
        return serialize_thread(db, application.chat_thread, current_user)

    thread = ChatThread(
        application_id=application.id,
        recruiter_id=current_user.id,
        job_seeker_id=application.job_seeker_id,
        job_id=application.job_id,
        status=ChatThreadStatus.ACTIVE.value,
        started_by_recruiter=True,
    )
    db.add(thread)
    db.flush()
    db.add(ChatMessage(thread_id=thread.id, sender_id=current_user.id, message_text=payload.message_text, is_read=False))
    add_timeline_event(
        db,
        application.id,
        "CHAT_STARTED",
        old_status=application.status,
        new_status=application.status,
        note="Recruiter started a chat",
        created_by_user_id=current_user.id,
    )
    create_notification(
        db,
        application.job_seeker_id,
        "Recruiter started a chat",
        f"{current_user.name} started a chat for {application.job.title}.",
        "CHAT_STARTED",
        f"/messages/{thread.id}",
    )
    db.commit()
    db.refresh(thread)
    thread = load_thread(db, thread.id)
    return serialize_thread(db, thread, current_user)


@router.get("", response_model=list[ChatThreadRead])
def chat_threads(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ChatThreadRead]:
    if current_user.role == UserRole.RECRUITER.value:
        statement = select(ChatThread).where(ChatThread.recruiter_id == current_user.id)
    elif current_user.role == UserRole.JOB_SEEKER.value:
        statement = select(ChatThread).where(ChatThread.job_seeker_id == current_user.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only recruiters and job seekers can use chats")

    threads = db.scalars(
        statement.options(
            joinedload(ChatThread.application),
            joinedload(ChatThread.job),
            joinedload(ChatThread.recruiter),
            joinedload(ChatThread.job_seeker),
        ).order_by(ChatThread.updated_at.desc(), ChatThread.id.desc())
    ).all()
    return [serialize_thread(db, thread, current_user) for thread in threads]


@router.get("/{thread_id}/messages", response_model=list[ChatMessageRead])
def chat_messages(
    thread_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ChatMessage]:
    thread = load_thread(db, thread_id)
    ensure_thread_reader(thread, current_user)
    return list(
        db.scalars(
            select(ChatMessage)
            .options(joinedload(ChatMessage.sender))
            .where(ChatMessage.thread_id == thread.id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        ).all()
    )


@router.post("/{thread_id}/messages", response_model=ChatMessageRead, status_code=status.HTTP_201_CREATED)
def send_message(
    thread_id: int,
    payload: ChatMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatMessage:
    thread = load_thread(db, thread_id)
    if is_admin_or_owner(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot send participant chat messages")
    ensure_thread_sender(thread, current_user)
    message = ChatMessage(thread_id=thread.id, sender_id=current_user.id, message_text=payload.message_text, is_read=False)
    thread.updated_at = now_naive()
    db.add(message)
    recipient_id = thread.job_seeker_id if current_user.id == thread.recruiter_id else thread.recruiter_id
    create_notification(
        db,
        recipient_id,
        "New message",
        f"{current_user.name} sent a new message about {thread.job.title}.",
        "NEW_MESSAGE",
        f"/messages/{thread.id}",
    )
    db.commit()
    db.refresh(message)
    return db.scalar(select(ChatMessage).options(joinedload(ChatMessage.sender)).where(ChatMessage.id == message.id)) or message


@router.put("/{thread_id}/read", response_model=ChatReadResponse)
def mark_thread_read(
    thread_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatReadResponse:
    thread = load_thread(db, thread_id)
    if current_user.id not in {thread.recruiter_id, thread.job_seeker_id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only chat participants can mark messages as read")
    unread_messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread.id)
        .where(ChatMessage.sender_id != current_user.id)
        .where(ChatMessage.is_read.is_(False))
    ).all()
    for message in unread_messages:
        message.is_read = True
        message.read_at = now_naive()
    db.commit()
    return ChatReadResponse(message="Messages marked as read")
