import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from app.models.enums import ActionRunStatus, ApprovalStatus, RiskLevel
from app.schemas.common import ORMModel


class ApprovedActionOut(ORMModel):
    id: uuid.UUID
    name: str
    description: str
    risk_level: RiskLevel
    requires_approval: bool
    enabled: bool


class ActionRunCreate(BaseModel):
    ticket_id: uuid.UUID
    device_id: uuid.UUID
    action_name: str
    input: dict[str, Any] = {}
    ai_suggested: bool = False


class ActionRunComplete(BaseModel):
    status: Literal[ActionRunStatus.completed, ActionRunStatus.failed]
    output: dict[str, Any] | None = None
    error_message: str | None = None


class ActionRunOut(ORMModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    device_id: uuid.UUID
    action_name: str
    requested_by_user_id: uuid.UUID
    approved_by_user_id: uuid.UUID | None
    approval_status: ApprovalStatus
    status: ActionRunStatus
    ai_suggested: bool
    input_json: dict[str, Any]
    output_json: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
