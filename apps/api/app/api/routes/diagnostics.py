import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, assert_client_access, assert_device_access, assert_ticket_access, is_staff
from app.models.device import Device
from app.models.ticket import Ticket
from app.models.diagnostic import DiagnosticResult, DiagnosticRun
from app.models.enums import DiagnosticRunStatus
from app.schemas.diagnostic import DiagnosticResultOut, DiagnosticRunCreate, DiagnosticRunOut
from app.services.audit import log_action

router = APIRouter(tags=["diagnostics"])


async def _run_to_out(db, run: DiagnosticRun) -> DiagnosticRunOut:
    results_result = await db.execute(
        select(DiagnosticResult).where(DiagnosticResult.diagnostic_run_id == run.id)
    )
    results = [DiagnosticResultOut.model_validate(r) for r in results_result.scalars().all()]
    out = DiagnosticRunOut.model_validate(run)
    out.results = results
    return out


@router.post("/diagnostics/runs", response_model=DiagnosticRunOut, status_code=status.HTTP_201_CREATED)
async def submit_diagnostic_run(payload: DiagnosticRunCreate, user: CurrentUser, db: DbSession):
    device = await db.get(Device, payload.device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    assert_device_access(user, device)
    if payload.ticket_id:
        ticket = await db.get(Ticket, payload.ticket_id)
        if ticket is None:
            raise HTTPException(404, "Ticket not found")
        assert_ticket_access(user, ticket)
        if ticket.client_id != device.client_id or ticket.device_id != device.id:
            raise HTTPException(400, "Diagnostic device must match the ticket device")

    now = datetime.now(timezone.utc)
    run = DiagnosticRun(
        client_id=device.client_id,
        ticket_id=payload.ticket_id,
        device_id=device.id,
        diagnostic_pack=payload.diagnostic_pack,
        status=DiagnosticRunStatus.completed,
        started_at=now,
        completed_at=now,
        created_by_user_id=user.id,
    )
    db.add(run)
    await db.flush()

    result = DiagnosticResult(diagnostic_run_id=run.id, result_json=payload.result, severity=payload.severity)
    db.add(result)

    await log_action(
        db,
        actor_user_id=user.id,
        client_id=device.client_id,
        action="diagnostic_run_submitted",
        entity_type="diagnostic_run",
        entity_id=str(run.id),
        metadata={"diagnostic_pack": payload.diagnostic_pack.value, "severity": payload.severity.value},
    )
    await db.commit()
    await db.refresh(run)
    return await _run_to_out(db, run)


@router.get("/diagnostics/runs/{run_id}", response_model=DiagnosticRunOut)
async def get_diagnostic_run(run_id: uuid.UUID, user: CurrentUser, db: DbSession):
    run = await db.get(DiagnosticRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic run not found")
    assert_client_access(user, run.client_id)
    device = await db.get(Device, run.device_id)
    if device is None:
        raise HTTPException(404, "Device not found")
    assert_device_access(user, device)
    if run.ticket_id:
        ticket = await db.get(Ticket, run.ticket_id)
        if ticket is None:
            raise HTTPException(404, "Ticket not found")
        assert_ticket_access(user, ticket)
    return await _run_to_out(db, run)


@router.get("/tickets/{ticket_id}/diagnostics", response_model=list[DiagnosticRunOut])
async def list_ticket_diagnostics(ticket_id: uuid.UUID, user: CurrentUser, db: DbSession):
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(404, "Ticket not found")
    assert_ticket_access(user, ticket)
    result = await db.execute(
        select(DiagnosticRun).where(DiagnosticRun.ticket_id == ticket_id, DiagnosticRun.client_id == ticket.client_id).order_by(DiagnosticRun.created_at.desc())
    )
    runs = result.scalars().all()
    if runs:
        assert_client_access(user, runs[0].client_id)
    return [await _run_to_out(db, r) for r in runs]
