import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ClientCreate(BaseModel):
    name: str
    contact_email: str | None = None


class ClientOut(ORMModel):
    id: uuid.UUID
    name: str
    contact_email: str | None
    is_active: bool
    is_internal: bool
    created_at: datetime
    updated_at: datetime
