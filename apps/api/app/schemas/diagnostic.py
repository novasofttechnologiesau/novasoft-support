import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import DiagnosticPack, DiagnosticRunStatus, Severity
from app.schemas.common import ORMModel


class DiagnosticRunCreate(BaseModel):
    device_id: uuid.UUID
    ticket_id: uuid.UUID | None = None
    diagnostic_pack: DiagnosticPack
    result: dict[str, Any]
    severity: Severity


class DiagnosticResultOut(ORMModel):
    id: uuid.UUID
    diagnostic_run_id: uuid.UUID
    result_json: dict[str, Any]
    severity: Severity
    created_at: datetime


class DiagnosticRunOut(ORMModel):
    id: uuid.UUID
    client_id: uuid.UUID
    ticket_id: uuid.UUID | None
    device_id: uuid.UUID
    diagnostic_pack: DiagnosticPack
    status: DiagnosticRunStatus
    started_at: datetime | None
    completed_at: datetime | None
    created_by_user_id: uuid.UUID
    results: list[DiagnosticResultOut] = []
