from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse
from app.services.audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: DbSession):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=user.id, role=user.role.value, client_id=user.client_id)
    await log_action(
        db,
        actor_user_id=user.id,
        client_id=user.client_id,
        action="login",
        entity_type="user",
        entity_id=str(user.id),
    )
    await db.commit()
    return LoginResponse(access_token=token)


@router.post("/logout")
async def logout(user: CurrentUser, db: DbSession):
    # JWTs are stateless in this MVP; logout is a client-side token discard plus an audit entry.
    # TODO: add a token blocklist if session revocation becomes a requirement.
    await log_action(
        db,
        actor_user_id=user.id,
        client_id=user.client_id,
        action="logout",
        entity_type="user",
        entity_id=str(user.id),
    )
    await db.commit()
    return {"detail": "Logged out"}


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser):
    return user
