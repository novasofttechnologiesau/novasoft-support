import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, assert_client_access, assert_ticket_access, is_staff, require_role
from app.models.ai_triage import AITriageResult
from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ai_triage import AITriageOut
from app.services.ai.service import AITriageService
from app.services.audit import log_action

router = APIRouter(tags=["ai"])

StaffUser = Annotated[User, Depends(require_role(UserRole.technician, UserRole.admin))]


@router.post("/ai/triage/{ticket_id}", response_model=AITriageOut, status_code=status.HTTP_201_CREATED)
async def run_ai_triage(ticket_id: uuid.UUID, user: StaffUser, db: DbSession):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    assert_ticket_access(user, ticket)

    service = AITriageService(db)
    triage = await service.triage_ticket(ticket_id)

    entry = AITriageResult(
        ticket_id=ticket.id,
        summary=triage.summary,
        likely_cause=triage.likely_cause,
        confidence=triage.confidence,
        risk_level=triage.risk_level,
        recommended_actions_json=[a.model_dump() for a in triage.recommended_actions],
        technician_notes=triage.technician_notes,
        user_reply_draft=triage.user_reply_draft,
        escalate=triage.escalate,
        raw_ai_response_json=triage.model_dump(mode="json"),
    )
    db.add(entry)

    ticket.ai_summary = triage.summary
    if ticket.status in (TicketStatus.new, TicketStatus.awaiting_diagnostics):
        ticket.status = TicketStatus.ai_triaged

    await log_action(
        db,
        actor_user_id=user.id,
        client_id=ticket.client_id,
        action="ai_triage_run",
        entity_type="ticket",
        entity_id=str(ticket.id),
        metadata={"risk_level": triage.risk_level.value, "escalate": triage.escalate},
    )
    await db.commit()
    await db.refresh(entry)
    if is_staff(user):
        return entry
    # Internal analysis stays staff-only; members receive only the draft intended for them.
    out = AITriageOut.model_validate(entry)
    out.summary = entry.user_reply_draft or "Your support team is reviewing this ticket."
    out.likely_cause = ""
    out.technician_notes = None
    out.recommended_actions_json = []
    return out


@router.get("/tickets/{ticket_id}/ai-triage", response_model=AITriageOut)
async def get_latest_ai_triage(ticket_id: uuid.UUID, user: CurrentUser, db: DbSession):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    assert_ticket_access(user, ticket)

    result = await db.execute(
        select(AITriageResult)
        .where(AITriageResult.ticket_id == ticket_id)
        .order_by(AITriageResult.created_at.desc())
        .limit(1)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No AI triage has been run for this ticket")
    if is_staff(user):
        return entry
    # Internal analysis stays staff-only; members receive only the draft intended for them.
    out = AITriageOut.model_validate(entry)
    out.summary = entry.user_reply_draft or "Your support team is reviewing this ticket."
    out.likely_cause = ""
    out.technician_notes = None
    out.recommended_actions_json = []
    return out
