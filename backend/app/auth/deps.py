from fastapi import Cookie, HTTPException

from app.auth.security import decode_token
from app.models import AdminUser

COOKIE_NAME = "admin_token"


async def require_admin(admin_token: str | None = Cookie(default=None)) -> AdminUser:
    email = decode_token(admin_token) if admin_token else None
    if email is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await AdminUser.find_one(AdminUser.email == email)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
