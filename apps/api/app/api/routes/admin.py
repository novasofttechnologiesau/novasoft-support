import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, is_staff, require_role
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.client import Client
from app.models.device import Device
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.audit_log import AuditLogOut
from app.schemas.client import ClientCreate, ClientOut
from app.schemas.device import DeviceCreate, DeviceOut
from app.schemas.user import UserCreate, UserOut
from app.services.audit import log_action

router = APIRouter(tags=["admin"])

AdminUser = Annotated[User, Depends(require_role(UserRole.admin))]
StaffUser = Annotated[User, Depends(require_role(UserRole.technician, UserRole.admin))]


@router.get("/clients", response_model=list[ClientOut])
async def list_clients(user: StaffUser, db: DbSession):
    result = await db.execute(select(Client).order_by(Client.name))
    return result.scalars().all()


@router.post("/clients", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(payload: ClientCreate, user: AdminUser, db: DbSession):
    client = Client(name=payload.name, contact_email=payload.contact_email)
    db.add(client)
    await db.flush()
    await log_action(
        db, actor_user_id=user.id, client_id=client.id, action="client_created",
        entity_type="client", entity_id=str(client.id),
    )
    await db.commit()
    await db.refresh(client)
    return client


@router.get("/users", response_model=list[UserOut])
async def list_users(user: StaffUser, db: DbSession):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, user: AdminUser, db: DbSession):
    existing = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    new_user = User(
        client_id=payload.client_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(new_user)
    await db.flush()
    await log_action(
        db, actor_user_id=user.id, client_id=new_user.client_id, action="user_created",
        entity_type="user", entity_id=str(new_user.id), metadata={"role": payload.role.value},
    )
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get("/devices", response_model=list[DeviceOut])
async def list_devices(user: CurrentUser, db: DbSession):
    stmt = select(Device).order_by(Device.device_name)
    if not is_staff(user):
        stmt = stmt.where(Device.owner_user_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/devices", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
async def create_device(payload: DeviceCreate, user: CurrentUser, db: DbSession):
    client_id = payload.client_id
    owner_user_id = payload.owner_user_id
    if not is_staff(user):
        # Self-service registration: the desktop app registers "this PC" for its own user.
        client_id = user.client_id
        owner_user_id = user.id
    elif client_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="client_id is required")

    device = Device(
        client_id=client_id,
        owner_user_id=owner_user_id,
        device_name=payload.device_name,
        hostname=payload.hostname,
        os_version=payload.os_version,
    )
    db.add(device)
    await db.flush()
    await log_action(
        db, actor_user_id=user.id, client_id=device.client_id, action="device_registered",
        entity_type="device", entity_id=str(device.id),
    )
    await db.commit()
    await db.refresh(device)
    return device


@router.get("/audit-logs", response_model=list[AuditLogOut])
async def list_audit_logs(user: AdminUser, db: DbSession, limit: int = 200):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 1000))
    )
    return result.scalars().all()
