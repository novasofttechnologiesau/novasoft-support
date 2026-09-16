import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import RiskLevel
from app.schemas.common import ORMModel


class RecommendedAction(BaseModel):
    action: str
    requires_approval: bool
    reason: str


class AITriageResponse(BaseModel):
    """The strict JSON contract returned by an AIProvider (mock or real)."""

    summary: str
    likely_cause: str
    confidence: float
    risk_level: RiskLevel
    recommended_actions: list[RecommendedAction] = []
    technician_notes: str | None = None
    user_reply_draft: str | None = None
    escalate: bool = False
    missing_information: list[str] = []


class AITriageOut(ORMModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    summary: str
    likely_cause: str
    confidence: float
    risk_level: RiskLevel
    recommended_actions_json: list[dict[str, Any]]
    technician_notes: str | None
    user_reply_draft: str | None
    escalate: bool
    created_at: datetime
