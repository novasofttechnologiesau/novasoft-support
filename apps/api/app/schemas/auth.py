import uuid

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole
from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(ORMModel):
    id: uuid.UUID
    client_id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
