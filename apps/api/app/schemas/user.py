import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole
from app.schemas.common import ORMModel
from app.schemas.password import NewPassword


class UserCreate(BaseModel):
    client_id: uuid.UUID
    email: EmailStr
    password: NewPassword
    full_name: str
    role: UserRole


class UserOut(ORMModel):
    id: uuid.UUID
    client_id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
