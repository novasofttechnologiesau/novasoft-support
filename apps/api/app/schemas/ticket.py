import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import TicketCategory, TicketPriority, TicketStatus
from app.schemas.common import ORMModel


class TicketCreate(BaseModel):
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority = TicketPriority.normal
    device_id: uuid.UUID | None = None


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_to_id: uuid.UUID | None = None
    device_id: uuid.UUID | None = None


class TicketOut(ORMModel):
    id: uuid.UUID
    client_id: uuid.UUID
    requester_id: uuid.UUID
    assigned_to_id: uuid.UUID | None
    device_id: uuid.UUID | None
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    ai_summary: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class TicketMessageCreate(BaseModel):
    body: str
    is_internal: bool = False


class TicketMessageOut(ORMModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_user_id: uuid.UUID
    body: str
    is_internal: bool
    created_at: datetime


class TicketAttachmentOut(ORMModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    uploaded_by_user_id: uuid.UUID
    original_file_name: str
    content_type: str
    size_bytes: int
    created_at: datetime
