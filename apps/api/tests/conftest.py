import os
import secrets
from types import SimpleNamespace

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Dedicated test database only. Never fall back to the application database.
TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if not TEST_URL or not TEST_URL.rsplit("/", 1)[-1].endswith("_test"):
    raise RuntimeError("Set TEST_DATABASE_URL to a dedicated PostgreSQL database ending in _test")
os.environ["DATABASE_URL"] = TEST_URL
os.environ["JWT_SECRET"] = secrets.token_urlsafe(48)
os.environ["AI_PROVIDER"] = "mock"
os.environ["ALLOW_EXTERNAL_AI"] = "false"

from app.main import app
from app.db.session import get_db
from app.core.security import create_access_token, hash_password
from app.models import Client, User, Device, Ticket, KnowledgeArticle, ApprovedAction
from app.models.enums import UserRole, TicketCategory, TicketPriority
from scripts.seed import seed_approved_actions


@pytest_asyncio.fixture
async def env(tmp_path, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    engine = create_async_engine(TEST_URL)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        db = AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
        clients = [Client(name="Example A"), Client(name="Example B")]
        db.add_all(clients)
        await db.flush()
        password = "Fictional-test-password-42"
        password_hash = hash_password(password)
        users = [
            User(client_id=clients[0].id, email="alice@example.com", full_name="Alice Example", role=UserRole.end_user, password_hash=password_hash),
            User(client_id=clients[0].id, email="peer@example.com", full_name="Peer Example", role=UserRole.end_user, password_hash=password_hash),
            User(client_id=clients[1].id, email="bob@example.com", full_name="Bob Example", role=UserRole.end_user, password_hash=password_hash),
            User(client_id=clients[0].id, email="staff@example.com", full_name="Staff Example", role=UserRole.technician, password_hash=password_hash),
            User(client_id=clients[0].id, email="admin@example.com", full_name="Admin Example", role=UserRole.admin, password_hash=password_hash),
        ]
        db.add_all(users)
        await db.flush()
        devices = [Device(client_id=u.client_id, owner_user_id=u.id, device_name=f"Demo {i}") for i, u in enumerate(users)]
        db.add_all(devices)
        await db.flush()
        tickets = [Ticket(client_id=u.client_id, requester_id=u.id, device_id=d.id, title=f"Printer issue {i}", description="Fictional test ticket", category=TicketCategory.printer_issue, priority=TicketPriority.normal) for i,(u,d) in enumerate(zip(users,devices))]
        db.add_all(tickets)
        for owner,title in [(None,"Global guide"),(clients[0].id,"Client A guide"),(clients[1].id,"Client B private guide")]:
            db.add(KnowledgeArticle(client_id=owner, title=title, body=title, category=TicketCategory.printer_issue, created_by_user_id=users[3].id))
        await seed_approved_actions(db)
        await db.commit()
        async def override_db():
            yield db
        app.dependency_overrides[get_db] = override_db
        def headers(i):
            u=users[i]
            return {"Authorization": "Bearer " + create_access_token(user_id=u.id, role=u.role.value, client_id=u.client_id)}
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
                yield SimpleNamespace(db=db, http=http, users=users, devices=devices, tickets=tickets, headers=headers, password=password, uploads=tmp_path)
        finally:
            app.dependency_overrides.clear()
            await db.close()
            await transaction.rollback()
    await engine.dispose()
