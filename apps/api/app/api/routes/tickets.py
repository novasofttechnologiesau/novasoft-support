import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, assert_client_access, assert_device_access, assert_ticket_access, is_staff
from app.models.enums import TicketStatus
from app.models.device import Device
from app.models.user import User
from app.models.ticket import Ticket
from app.models.ticket_attachment import TicketAttachment
from app.models.ticket_message import TicketMessage
from app.schemas.ticket import (
    TicketAttachmentOut,
    TicketCreate,
    TicketMessageCreate,
    TicketMessageOut,
    TicketOut,
    TicketUpdate,
)
from app.services.audit import log_action

router = APIRouter(prefix="/tickets", tags=["tickets"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".txt", ".log", ".zip"}
MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024


def _sanitize_filename(filename: str) -> tuple[str, str]:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' is not allowed",
        )
    stored_name = f"{uuid.uuid4()}{ext}"
    return stored_name, ext


async def _get_ticket_or_404(db: DbSession, ticket_id: uuid.UUID) -> Ticket:
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


def _assert_ticket_access(user, ticket: Ticket) -> None:
    assert_ticket_access(user, ticket)


@router.get("", response_model=list[TicketOut])
async def list_tickets(user: CurrentUser, db: DbSession):
    stmt = select(Ticket).order_by(Ticket.created_at.desc())
    if is_staff(user):
        pass  # staff can see all clients' tickets in this MVP support-org model
    else:
        stmt = stmt.where(Ticket.requester_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, user: CurrentUser, db: DbSession):
    if payload.device_id:
        device = await db.get(Device, payload.device_id)
        if device is None:
            raise HTTPException(404, "Device not found")
        assert_device_access(user, device)
        if device.client_id != user.client_id:
            raise HTTPException(400, "Device must belong to the ticket client")
    ticket = Ticket(
        client_id=user.client_id,
        requester_id=user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        device_id=payload.device_id,
        status=TicketStatus.new,
    )
    db.add(ticket)
    await db.flush()
    await log_action(
        db,
        actor_user_id=user.id,
        client_id=user.client_id,
        action="ticket_created",
        entity_type="ticket",
        entity_id=str(ticket.id),
        metadata={"category": payload.category.value, "priority": payload.priority.value},
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(ticket_id: uuid.UUID, user: CurrentUser, db: DbSession):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _assert_ticket_access(user, ticket)
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(ticket_id: uuid.UUID, payload: TicketUpdate, user: CurrentUser, db: DbSession):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _assert_ticket_access(user, ticket)

    if not is_staff(user) and ({"assigned_to_id", "status"} & payload.model_fields_set):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only technicians/admins can change status or assignment",
        )

    if payload.device_id:
        device = await db.get(Device, payload.device_id)
        if device is None:
            raise HTTPException(404, "Device not found")
        assert_device_access(user, device)
        if device.client_id != ticket.client_id:
            raise HTTPException(400, "Device must belong to the ticket client")
    if payload.assigned_to_id:
        assignee = await db.get(User, payload.assigned_to_id)
        if assignee is None or not assignee.is_active or not is_staff(assignee):
            raise HTTPException(400, "Assign tickets only to active staff")
    if any(getattr(payload, key) is None for key in ("status", "priority") if key in payload.model_fields_set):
        raise HTTPException(422, "Status and priority cannot be null")
    changes = payload.model_dump(exclude_unset=True, mode="json")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    if payload.status == TicketStatus.resolved:
        from datetime import datetime, timezone

        ticket.resolved_at = datetime.now(timezone.utc)

    await log_action(
        db,
        actor_user_id=user.id,
        client_id=ticket.client_id,
        action="ticket_updated",
        entity_type="ticket",
        entity_id=str(ticket.id),
        metadata=changes,
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/messages", response_model=TicketMessageOut, status_code=status.HTTP_201_CREATED)
async def add_ticket_message(
    ticket_id: uuid.UUID, payload: TicketMessageCreate, user: CurrentUser, db: DbSession
):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _assert_ticket_access(user, ticket)

    if payload.is_internal and not is_staff(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only technicians/admins can add internal notes"
        )

    message = TicketMessage(
        ticket_id=ticket.id, author_user_id=user.id, body=payload.body, is_internal=payload.is_internal
    )
    db.add(message)
    await log_action(
        db,
        actor_user_id=user.id,
        client_id=ticket.client_id,
        action="ticket_message_added",
        entity_type="ticket",
        entity_id=str(ticket.id),
        metadata={"is_internal": payload.is_internal},
    )
    await db.commit()
    await db.refresh(message)
    return message


@router.get("/{ticket_id}/messages", response_model=list[TicketMessageOut])
async def list_ticket_messages(ticket_id: uuid.UUID, user: CurrentUser, db: DbSession):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _assert_ticket_access(user, ticket)

    stmt = select(TicketMessage).where(TicketMessage.ticket_id == ticket.id).order_by(TicketMessage.created_at)
    if not is_staff(user):
        stmt = stmt.where(TicketMessage.is_internal.is_(False))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/{ticket_id}/attachments", response_model=TicketAttachmentOut, status_code=status.HTTP_201_CREATED
)
async def upload_ticket_attachment(
    ticket_id: uuid.UUID, user: CurrentUser, db: DbSession, file: UploadFile
):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _assert_ticket_access(user, ticket)

    stored_name, _ext = _sanitize_filename(file.filename or "upload")
    try:
        contents = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds the {settings.MAX_UPLOAD_MB}MB upload limit",
        )

    dest_dir = Path(settings.UPLOAD_DIR) / str(ticket.client_id) / str(ticket.id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / stored_name
    dest_path.write_bytes(contents)

    attachment = TicketAttachment(
        ticket_id=ticket.id,
        uploaded_by_user_id=user.id,
        stored_file_name=stored_name,
        original_file_name=Path(file.filename or "upload").name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        storage_path=str(dest_path),
    )
    db.add(attachment)
    await log_action(
        db,
        actor_user_id=user.id,
        client_id=ticket.client_id,
        action="ticket_attachment_uploaded",
        entity_type="ticket",
        entity_id=str(ticket.id),
        metadata={"file_name": attachment.original_file_name, "size_bytes": attachment.size_bytes},
    )
    await db.commit()
    await db.refresh(attachment)
    return attachment


@router.get("/{ticket_id}/attachments", response_model=list[TicketAttachmentOut])
async def list_ticket_attachments(ticket_id: uuid.UUID, user: CurrentUser, db: DbSession):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _assert_ticket_access(user, ticket)
    result = await db.execute(
        select(TicketAttachment).where(TicketAttachment.ticket_id == ticket.id).order_by(TicketAttachment.created_at)
    )
    return result.scalars().all()
