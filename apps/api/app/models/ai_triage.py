import uuid

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import RiskLevel


class AITriageResult(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "ai_triage_results"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    likely_cause: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"), nullable=False)
    recommended_actions_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    technician_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_reply_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_ai_response_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
