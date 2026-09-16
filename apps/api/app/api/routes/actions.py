import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, assert_client_access, assert_ticket_access, assert_device_access, is_staff
from app.models.action_run import ActionRun
from app.models.approved_action import ApprovedAction
from app.models.device import Device
from app.models.enums import ActionRunStatus, ApprovalStatus, TicketStatus
from app.models.ticket import Ticket
from app.schemas.action import ActionRunComplete, ActionRunCreate, ActionRunOut, ApprovedActionOut
from app.services.actions.registry import get_action
from app.services.audit import log_action

router = APIRouter(tags=["actions"])


@router.get("/approved-actions", response_model=list[ApprovedActionOut])
async def list_approved_actions(user: CurrentUser, db: DbSession):
    result = await db.execute(select(ApprovedAction).order_by(ApprovedAction.name))
    return result.scalars().all()


@router.post("/actions/run", response_model=ActionRunOut, status_code=status.HTTP_201_CREATED)
async def run_action(payload: ActionRunCreate, user: CurrentUser, db: DbSession):
    definition = get_action(payload.action_name)
    if definition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown action")

    db_action = (
        await db.execute(select(ApprovedAction).where(ApprovedAction.name == payload.action_name))
    ).scalar_one_or_none()
    if db_action is None or not db_action.enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action is not enabled")

    if not definition.implemented:
        raise HTTPException(409, "This action is unavailable in the community preview")
    if user.role not in definition.allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your role cannot run this action")

    ticket = await db.get(Ticket, payload.ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    device = await db.get(Device, payload.device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    assert_ticket_access(user, ticket)
    assert_device_access(user, device)
    if device.client_id != ticket.client_id or ticket.device_id != device.id:
        raise HTTPException(400, "Action device must match the ticket device")

    if not is_staff(user) and device.owner_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only act on your own device")

    requires_approval = definition.requires_approval or db_action.requires_approval
    approval_status = ApprovalStatus.pending if requires_approval else ApprovalStatus.not_required
    run_status = ActionRunStatus.blocked if requires_approval else ActionRunStatus.approved

    action_run = ActionRun(
        ticket_id=ticket.id,
        device_id=device.id,
        action_name=payload.action_name,
        requested_by_user_id=user.id,
        approval_status=approval_status,
        status=run_status,
        ai_suggested=payload.ai_suggested,
        input_json=payload.input,
    )
    db.add(action_run)
    await db.flush()

    if not requires_approval and not definition.implemented:
        action_run.status = ActionRunStatus.failed
        action_run.error_message = "This action is registered but has no implemented handler yet."
        action_run.completed_at = datetime.now(timezone.utc)
    elif not requires_approval and definition.executed_by == "server":
        # escalate_ticket is the only server-executed action today: no device round-trip needed.
        if payload.action_name == "escalate_ticket":
            ticket.status = TicketStatus.waiting_for_technician
            action_run.output_json = {"ticket_status": ticket.status.value}
        action_run.status = ActionRunStatus.completed
        action_run.completed_at = datetime.now(timezone.utc)

    await log_action(
        db,
        actor_user_id=user.id,
        client_id=ticket.client_id,
        action="action_run_requested",
        entity_type="action_run",
        entity_id=str(action_run.id),
        metadata={
            "action_name": payload.action_name,
            "ai_suggested": payload.ai_suggested,
            "requires_approval": db_action.requires_approval,
        },
    )
    await db.commit()
    await db.refresh(action_run)
    return action_run


@router.post("/actions/{action_run_id}/approve", response_model=ActionRunOut)
async def approve_action(action_run_id: uuid.UUID, user: CurrentUser, db: DbSession):
    if not is_staff(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only technicians/admins can approve actions")

    action_run = await db.get(ActionRun, action_run_id)
    if action_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action run not found")
    if action_run.approval_status != ApprovalStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action run is not pending approval")

    definition = get_action(action_run.action_name)
    if definition is None or not definition.implemented:
        raise HTTPException(409, "This action is unavailable in the community preview")
    action_run.approval_status = ApprovalStatus.approved
    action_run.status = ActionRunStatus.approved
    action_run.approved_by_user_id = user.id

    ticket = await db.get(Ticket, action_run.ticket_id)
    await log_action(
        db,
        actor_user_id=user.id,
        client_id=ticket.client_id if ticket else None,
        action="action_run_approved",
        entity_type="action_run",
        entity_id=str(action_run.id),
        metadata={"action_name": action_run.action_name},
    )
    await db.commit()
    await db.refresh(action_run)
    return action_run


@router.post("/actions/{action_run_id}/complete", response_model=ActionRunOut)
async def complete_action(
    action_run_id: uuid.UUID, payload: ActionRunComplete, user: CurrentUser, db: DbSession
):
    """Called by the desktop app after it has locally executed an approved, device-executed
    action, reporting back the structured result for audit purposes."""
    action_run = await db.get(ActionRun, action_run_id)
    if action_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action run not found")
    if action_run.status != ActionRunStatus.approved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action run is not in an approved state")
    if not is_staff(user) and action_run.requested_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your action run")

    definition = get_action(action_run.action_name)
    if definition is None or not definition.implemented or definition.executed_by != "device":
        raise HTTPException(409, "This action cannot be completed by a device")
    action_run.status = payload.status
    action_run.output_json = payload.output
    action_run.error_message = payload.error_message
    action_run.completed_at = datetime.now(timezone.utc)

    ticket = await db.get(Ticket, action_run.ticket_id)
    await log_action(
        db,
        actor_user_id=user.id,
        client_id=ticket.client_id if ticket else None,
        action="action_run_completed",
        entity_type="action_run",
        entity_id=str(action_run.id),
        metadata={"action_name": action_run.action_name, "status": payload.status.value},
    )
    await db.commit()
    await db.refresh(action_run)
    return action_run


@router.get("/tickets/{ticket_id}/actions", response_model=list[ActionRunOut])
async def list_ticket_actions(ticket_id: uuid.UUID, user: CurrentUser, db: DbSession):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    assert_ticket_access(user, ticket)

    result = await db.execute(
        select(ActionRun).where(ActionRun.ticket_id == ticket_id).order_by(ActionRun.created_at.desc())
    )
    return result.scalars().all()
