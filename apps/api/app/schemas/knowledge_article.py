import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import TicketCategory
from app.schemas.common import ORMModel


class KnowledgeArticleCreate(BaseModel):
    title: str
    body: str
    category: TicketCategory | None = None
    client_id: uuid.UUID | None = None


class KnowledgeArticleOut(ORMModel):
    id: uuid.UUID
    client_id: uuid.UUID | None
    title: str
    body: str
    category: TicketCategory | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
