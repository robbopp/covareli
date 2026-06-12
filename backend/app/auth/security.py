from datetime import timedelta

import bcrypt
import jwt

from app.config import config
from app.timeutil import utcnow


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": utcnow() + timedelta(hours=config.jwt_expires_hours),
    }
    return jwt.encode(payload, config.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=["HS256"])
        return payload["sub"]
    except jwt.InvalidTokenError:
        return None
