import jwt as pyjwt

from app.auth.security import create_token, decode_token, hash_password, verify_password
from app.config import config
from app.models import AdminUser


def test_password_hash_roundtrip():
    h = hash_password("secret123")
    assert h != "secret123"
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    token = create_token("admin@test.ro")
    assert decode_token(token) == "admin@test.ro"
    assert decode_token("garbage") is None


def test_decode_token_without_sub_returns_none():
    token = pyjwt.encode({"exp": 9999999999}, config.jwt_secret, algorithm="HS256")
    assert decode_token(token) is None


async def make_admin(email="admin@test.ro", password="secret123"):
    await AdminUser(email=email, password_hash=hash_password(password)).insert()


async def test_login_sets_cookie_and_me_works(api):
    await make_admin()
    resp = await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    assert resp.status_code == 200
    assert "admin_token" in resp.cookies
    me = await api.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "admin@test.ro"


async def test_login_wrong_password_rejected(api):
    await make_admin()
    resp = await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "nope"}
    )
    assert resp.status_code == 401


async def test_me_without_cookie_rejected(api):
    resp = await api.get("/api/auth/me")
    assert resp.status_code == 401


async def test_logout_clears_cookie(api):
    await make_admin()
    await api.post("/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"})
    await api.post("/api/auth/logout")
    resp = await api.get("/api/auth/me")
    assert resp.status_code == 401


async def test_change_password(api):
    await make_admin()
    await api.post("/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"})
    resp = await api.post(
        "/api/auth/change-password",
        json={"current_password": "secret123", "new_password": "newsecret456"},
    )
    assert resp.status_code == 200
    resp = await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "newsecret456"}
    )
    assert resp.status_code == 200


async def test_login_throttled_after_too_many_attempts(api):
    from app.auth.routes import MAX_ATTEMPTS, _attempts

    _attempts.clear()
    await make_admin()
    for _ in range(MAX_ATTEMPTS):
        resp = await api.post(
            "/api/auth/login", json={"email": "admin@test.ro", "password": "nope"}
        )
        assert resp.status_code == 401
    resp = await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    assert resp.status_code == 429
    _attempts.clear()


async def test_change_password_rejects_short_password(api):
    await make_admin()
    await api.post("/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"})
    resp = await api.post(
        "/api/auth/change-password",
        json={"current_password": "secret123", "new_password": "short"},
    )
    assert resp.status_code == 400
