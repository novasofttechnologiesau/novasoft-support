import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class DeviceCreate(BaseModel):
    # client_id/owner_user_id are only honored when an admin/technician creates the device;
    # the API forces both to the caller's own identity for self-service registration (see
    # POST /devices), so end users never need to (or are able to) supply them.
    client_id: uuid.UUID | None = None
    owner_user_id: uuid.UUID | None = None
    device_name: str
    hostname: str | None = None
    os_version: str | None = None


class DeviceOut(ORMModel):
    id: uuid.UUID
    client_id: uuid.UUID
    owner_user_id: uuid.UUID | None
    device_name: str
    hostname: str | None
    os_version: str | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime
