import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.core.config import Settings
from app.models import TicketMessage, DiagnosticRun, DiagnosticResult, ApprovedAction, AITriageResult
from app.models.enums import DiagnosticPack, DiagnosticRunStatus, Severity
from app.services.ai.service import _build_context
from app.services.ai.context import TriageContext
from app.services.ai.deepseek_provider import _build_user_prompt
from app.services.ai.factory import get_ai_provider
from app.services.ai.mock_provider import MockAIProvider


async def test_login_and_staff_roles(env):
    e=env
    result=await e.http.post("/auth/login",json={"email": e.users[0].email,"password":e.password})
    assert result.status_code==200
    assert (await e.http.get("/auth/me",headers={"Authorization":"Bearer "+result.json()["access_token"]})).status_code==200
    assert (await e.http.post("/auth/login",json={"email":e.users[0].email,"password":"wrong"})).status_code==401
    assert (await e.http.get("/tickets")).status_code==401
    assert (await e.http.get("/audit-logs",headers=e.headers(0))).status_code==403
    assert (await e.http.get("/audit-logs",headers=e.headers(4))).status_code==200
    assert (await e.http.get("/users",headers=e.headers(0))).status_code==403


@pytest.mark.parametrize("other",[1,2])
async def test_ticket_subresources_are_owner_scoped(env,other):
    e=env; ticket=e.tickets[other]
    for suffix in ["", "/messages", "/attachments", "/diagnostics", "/actions", "/ai-triage"]:
        response=await e.http.get(f"/tickets/{ticket.id}{suffix}",headers=e.headers(0))
        assert response.status_code==403,(suffix,response.text)
    assert (await e.http.get(f"/tickets/{ticket.id}",headers=e.headers(3))).status_code==200


async def test_ticket_device_links_and_explicit_null_assignment(env):
    e=env; body={"title":"Example", "description":"Example", "category":"printer_issue"}
    for i in [1,2]:
        assert (await e.http.post("/tickets",json={**body,"device_id":str(e.devices[i].id)},headers=e.headers(0))).status_code==403
        assert (await e.http.patch(f"/tickets/{e.tickets[0].id}",json={"device_id":str(e.devices[i].id)},headers=e.headers(0))).status_code==403
    assert (await e.http.patch(f"/tickets/{e.tickets[0].id}",json={"assigned_to_id":None},headers=e.headers(0))).status_code==403
    result=await e.http.patch(f"/tickets/{e.tickets[0].id}",json={"status":"in_progress","assigned_to_id":str(e.users[3].id)},headers=e.headers(3))
    assert result.status_code==200,result.text
    result=await e.http.post("/tickets",json={**body,"device_id":str(e.devices[0].id)},headers=e.headers(0))
    assert result.status_code==201,result.text


async def test_internal_notes_are_hidden(env):
    e=env; url=f"/tickets/{e.tickets[0].id}/messages"
    assert (await e.http.post(url,json={"body":"staff-only","is_internal":True},headers=e.headers(3))).status_code==201
    assert (await e.http.post(url,json={"body":"forged","is_internal":True},headers=e.headers(0))).status_code==403
    assert (await e.http.get(url,headers=e.headers(0))).json()==[]
    assert len((await e.http.get(url,headers=e.headers(3))).json())==1


async def test_diagnostics_cannot_cross_owner_or_ticket(env):
    e=env
    def body(device,ticket):
        return {"device_id":str(device.id),"ticket_id":str(ticket.id),"diagnostic_pack":"device_health_basic","severity":"ok","result":{"cpu_usage_percent":10}}
    for i in [1,2]:
        assert (await e.http.post("/diagnostics/runs",json=body(e.devices[i],e.tickets[0]),headers=e.headers(0))).status_code==403
        assert (await e.http.post("/diagnostics/runs",json=body(e.devices[0],e.tickets[i]),headers=e.headers(0))).status_code==403
    assert (await e.http.post("/diagnostics/runs",json=body(e.devices[0],e.tickets[2]),headers=e.headers(3))).status_code==400
    result=await e.http.post("/diagnostics/runs",json=body(e.devices[0],e.tickets[0]),headers=e.headers(0))
    assert result.status_code==201,result.text
    run=result.json()
    assert (await e.http.get(f"/diagnostics/runs/{run['id']}",headers=e.headers(1))).status_code==403
    assert (await e.http.get(f"/diagnostics/runs/{run['id']}",headers=e.headers(0))).status_code==200


async def test_knowledge_and_ai_context_are_client_scoped(env):
    e=env
    articles=(await e.http.get("/knowledge-articles",headers=e.headers(0))).json()
    assert {a["title"] for a in articles}=={"Global guide","Client A guide"}
    context=await _build_context(e.db,e.tickets[0])
    assert {a["title"] for a in context.knowledge_articles}=={"Global guide","Client A guide"}
    result=await e.http.post(f"/ai/triage/{e.tickets[0].id}",headers=e.headers(3))
    assert result.status_code==201,result.text
    assert result.json()["technician_notes"]
    member=await e.http.get(f"/tickets/{e.tickets[0].id}/ai-triage",headers=e.headers(0))
    assert member.status_code==200
    assert member.json()["technician_notes"] is None
    assert member.json()["recommended_actions_json"]==[]
    assert (await e.http.post(f"/ai/triage/{e.tickets[0].id}",headers=e.headers(0))).status_code==403


async def test_native_actions_fail_closed_and_escalation_works(env):
    e=env; base={"ticket_id":str(e.tickets[0].id),"device_id":str(e.devices[0].id)}
    for name in ["restart_print_spooler","flush_dns","restart_onedrive","kill_process"]:
        # Even a stale enabled database row cannot enable an unimplemented handler.
        row=(await e.db.execute(select(ApprovedAction).where(ApprovedAction.name==name))).scalar_one()
        row.enabled=True
        await e.db.commit()
        response=await e.http.post("/actions/run",json={**base,"action_name":name},headers=e.headers(0))
        assert response.status_code==409,response.text
    assert (await e.http.post("/actions/run",json={**base,"action_name":"arbitrary_shell"},headers=e.headers(0))).status_code==404
    response=await e.http.post("/actions/run",json={**base,"action_name":"escalate_ticket"},headers=e.headers(0))
    assert response.status_code==201,response.text
    assert response.json()["status"]=="completed"
    assert (await e.http.get(f"/tickets/{e.tickets[0].id}",headers=e.headers(0))).json()["status"]=="waiting_for_technician"


async def test_action_ticket_ownership(env):
    e=env
    response=await e.http.post("/actions/run",json={"ticket_id":str(e.tickets[1].id),"device_id":str(e.devices[0].id),"action_name":"escalate_ticket"},headers=e.headers(0))
    assert response.status_code==403


async def test_upload_limits_and_generated_storage_names(env,monkeypatch):
    from app.api.routes import tickets
    monkeypatch.setattr(tickets,"MAX_UPLOAD_BYTES",8)
    e=env;url=f"/tickets/{e.tickets[0].id}/attachments"
    assert (await e.http.post(url,files={"file":("evil.exe",b"x")},headers=e.headers(0))).status_code==400
    assert (await e.http.post(url,files={"file":("large.txt",b"x"*9)},headers=e.headers(0))).status_code==400
    result=await e.http.post(url,files={"file":("../../note.txt",b"hello")},headers=e.headers(0))
    assert result.status_code==201,result.text
    stored=list(e.uploads.rglob("*.txt"))
    assert len(stored)==1 and stored[0].name!="note.txt"
    assert stored[0].read_bytes()==b"hello"


def test_external_ai_requires_explicit_opt_in(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings,"AI_PROVIDER","deepseek")
    monkeypatch.setattr(settings,"DEEPSEEK_API_KEY","fake-test-key")
    monkeypatch.setattr(settings,"ALLOW_EXTERNAL_AI",False)
    assert isinstance(get_ai_provider(),MockAIProvider)


def test_ai_redacts_nested_secrets_and_identity():
    context=TriageContext(ticket_title="password=topsecret",ticket_description="bearer confidential",ticket_category="other",ticket_priority="normal",device_name="private-machine",requester_name="Private Person",diagnostic_results=[{"api_key":"dont-send-this","details":"secret=hidden"}],knowledge_articles=[{"body":"token=private-token"}])
    prompt=_build_user_prompt(context)
    for secret in ["topsecret","confidential","private-machine","Private Person","dont-send-this","hidden","private-token"]:
        assert secret not in prompt


def test_signing_secret_and_password_validation():
    from app.schemas.password import validate_password
    for secret in ["", "change_me_to_a_long_random_string", "x"*64]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None,DATABASE_URL="postgresql://localhost/test",JWT_SECRET=secret)
    with pytest.raises(ValueError):validate_password("short")
    with pytest.raises(ValueError):validate_password("x"*73)


async def test_body_limit_covers_chunked_uploads():
    from app.core.body_limit import BodyLimitMiddleware
    called=False; sent=[]
    async def inner(scope,receive,send):
        nonlocal called
        called=True
    parts=iter([{"type":"http.request","body":b"1234","more_body":True},{"type":"http.request","body":b"5678","more_body":False}])
    async def receive():return next(parts)
    async def send(message):sent.append(message)
    await BodyLimitMiddleware(inner,5)({"type":"http"},receive,send)
    assert not called
    assert sent[0]["status"]==413
