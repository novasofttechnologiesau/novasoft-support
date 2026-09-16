import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError, AttributeError):
        raise credentials_error

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):
    async def _checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return _checker


def is_staff(user: User) -> bool:
    return user.role in (UserRole.admin, UserRole.technician)


def assert_client_access(user: User, client_id: uuid.UUID) -> None:
    """End users may only ever touch data scoped to their own client. Staff (technician/admin)
    can access any client's data in this MVP (single internal support org model)."""
    if not is_staff(user) and user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this client's data",
        )


def assert_ticket_access(user, ticket) -> None:
    assert_client_access(user, ticket.client_id)
    if not is_staff(user) and ticket.requester_id != user.id:
        raise HTTPException(403, "Not your ticket")


def assert_device_access(user, device) -> None:
    assert_client_access(user, device.client_id)
    if not is_staff(user) and device.owner_user_id != user.id:
        raise HTTPException(403, "Not your device")
