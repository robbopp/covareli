import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app.auth.deps import COOKIE_NAME, require_admin
from app.auth.security import create_token, hash_password, verify_password
from app.config import config
from app.models import AdminUser

router = APIRouter(prefix="/api/auth", tags=["auth"])

_DUMMY_HASH = hash_password("dummy-password-for-timing-equalization")

MAX_ATTEMPTS = 10
WINDOW_SECONDS = 300
_attempts: dict[str, list[float]] = defaultdict(list)


def _throttle(ip: str) -> None:
    now = time.monotonic()
    _attempts[ip] = [t for t in _attempts[ip] if now - t < WINDOW_SECONDS]
    if len(_attempts[ip]) >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts")
    _attempts[ip].append(now)


class LoginBody(BaseModel):
    email: str
    password: str


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
async def login(body: LoginBody, request: Request, response: Response):
    _throttle(request.client.host if request.client else "unknown")
    user = await AdminUser.find_one(AdminUser.email == body.email)
    target_hash = user.password_hash if user is not None else _DUMMY_HASH
    if not verify_password(body.password, target_hash) or user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    response.set_cookie(
        COOKIE_NAME,
        create_token(user.email),
        httponly=True,
        secure=config.cookie_secure,
        samesite="lax",
        max_age=config.jwt_expires_hours * 3600,
    )
    return {"email": user.email}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        COOKIE_NAME,
        httponly=True,
        secure=config.cookie_secure,
        samesite="lax",
    )
    return {"ok": True}


@router.get("/me")
async def me(user: AdminUser = Depends(require_admin)):
    return {"email": user.email}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordBody, user: AdminUser = Depends(require_admin)
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is wrong")
    if len(body.new_password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters")
    user.password_hash = hash_password(body.new_password)
    await user.save()
    return {"ok": True}
