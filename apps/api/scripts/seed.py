"""Idempotent dev/demo seed data.

There is no public self-registration endpoint (by design -- see docs/security.md), so this
script is how the first users get created. Safe to re-run: it looks up by unique fields
before inserting.

Usage: `python -m scripts.seed` (from apps/api, with the venv active and DATABASE_URL set).
"""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.approved_action import ApprovedAction
from app.models.client import Client
from app.models.device import Device
from app.models.enums import UserRole
from app.models.user import User
from app.services.actions.registry import ACTION_REGISTRY

DEV_PASSWORD = settings.DEMO_SEED_PASSWORD


async def get_or_create_client(db, *, name: str, is_internal: bool, contact_email: str | None = None) -> Client:
    existing = (await db.execute(select(Client).where(Client.name == name))).scalar_one_or_none()
    if existing:
        return existing
    client = Client(name=name, is_internal=is_internal, contact_email=contact_email)
    db.add(client)
    await db.flush()
    return client


async def get_or_create_user(db, *, client_id, email: str, full_name: str, role: UserRole) -> User:
    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        return existing
    user = User(
        client_id=client_id,
        email=email,
        password_hash=hash_password(DEV_PASSWORD),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    await db.flush()
    return user


async def get_or_create_device(db, *, client_id, owner_user_id, device_name: str) -> Device:
    existing = (
        await db.execute(select(Device).where(Device.device_name == device_name))
    ).scalar_one_or_none()
    if existing:
        return existing
    device = Device(client_id=client_id, owner_user_id=owner_user_id, device_name=device_name)
    db.add(device)
    await db.flush()
    return device


async def seed_approved_actions(db) -> None:
    for name, definition in ACTION_REGISTRY.items():
        existing = (
            await db.execute(select(ApprovedAction).where(ApprovedAction.name == name))
        ).scalar_one_or_none()
        if existing:
            continue
        db.add(
            ApprovedAction(
                name=name,
                description=definition.description,
                risk_level=definition.risk_level,
                requires_approval=definition.requires_approval,
                enabled=definition.implemented,
            )
        )


async def main() -> None:
    if not settings.ALLOW_DEMO_SEED or len(DEV_PASSWORD) < 16:
        raise SystemExit("Demo seeding requires ALLOW_DEMO_SEED=true and a generated DEMO_SEED_PASSWORD (16+ characters)")
    async with AsyncSessionLocal() as db:
        novasoft = await get_or_create_client(db, name="NovaSoft Technologies (Internal)", is_internal=True)
        demo_client = await get_or_create_client(
            db, name="Acme Co", is_internal=False, contact_email="it@acme.example"
        )

        admin = await get_or_create_user(
            db, client_id=novasoft.id, email="admin@novasoft.example", full_name="NovaSoft Admin", role=UserRole.admin
        )
        technician = await get_or_create_user(
            db,
            client_id=novasoft.id,
            email="tech@novasoft.example",
            full_name="NovaSoft Technician",
            role=UserRole.technician,
        )
        end_user = await get_or_create_user(
            db, client_id=demo_client.id, email="user@acme.example", full_name="Alex Example", role=UserRole.end_user
        )

        await get_or_create_device(
            db, client_id=demo_client.id, owner_user_id=end_user.id, device_name="ACME-ALEX-PC01"
        )

        await seed_approved_actions(db)

        await db.commit()

    print("Seed complete.")
    print(f"  Admin:      admin@novasoft.example (password is in your local .env)")
    print(f"  Technician: tech@novasoft.example (password is in your local .env)")
    print(f"  End user:   user@acme.example (password is in your local .env)")


if __name__ == "__main__":
    asyncio.run(main())
