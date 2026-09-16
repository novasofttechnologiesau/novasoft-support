import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import DiagnosticPack, DiagnosticRunStatus, Severity


class DiagnosticRun(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "diagnostic_runs"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False
    )
    diagnostic_pack: Mapped[DiagnosticPack] = mapped_column(
        Enum(DiagnosticPack, name="diagnostic_pack"), nullable=False
    )
    status: Mapped[DiagnosticRunStatus] = mapped_column(
        Enum(DiagnosticRunStatus, name="diagnostic_run_status"),
        nullable=False,
        default=DiagnosticRunStatus.completed,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )


class DiagnosticResult(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "diagnostic_results"

    diagnostic_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("diagnostic_runs.id"), nullable=False
    )
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity, name="severity"), nullable=False)
