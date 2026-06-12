import pytest_asyncio

from app.auth.security import hash_password
from app.models import AdminUser, ContactMessage


@pytest_asyncio.fixture
async def admin(api):
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    return api


async def test_contact_form_saves_message(api):
    resp = await api.post("/api/contact", json={
        "name": "Ion Pop", "email": "ion@example.com",
        "phone": "0744111222", "message": "Aveți mașini libere în iulie?",
    })
    assert resp.status_code == 201
    assert await ContactMessage.find_all().count() == 1


async def test_contact_form_validates(api):
    resp = await api.post("/api/contact", json={"name": "", "email": "x", "message": ""})
    assert resp.status_code == 422


async def test_admin_lists_and_marks_messages(admin):
    await admin.post("/api/contact", json={
        "name": "Ion Pop", "email": "ion@example.com", "message": "Salut",
    })
    resp = await admin.get("/api/admin/messages")
    assert resp.status_code == 200
    msg = resp.json()[0]
    assert msg["read"] is False

    resp = await admin.put(f"/api/admin/messages/{msg['id']}/read", json={"read": True})
    assert resp.status_code == 200
    assert resp.json()["read"] is True


async def test_messages_require_auth(api):
    resp = await api.get("/api/admin/messages")
    assert resp.status_code == 401


async def test_settings_roundtrip(admin):
    resp = await admin.get("/api/admin/settings")
    assert resp.status_code == 200
    assert resp.json()["payment_mode"] == "full"

    resp = await admin.put("/api/admin/settings", json={
        "payment_mode": "full", "advance_value": 0,
        "contact_phone": "+40 700 000 000",
        "contact_email": "office@covareli.ro",
        "contact_address": "Adresa nouă",
    })
    assert resp.status_code == 200
    assert resp.json()["contact_phone"] == "+40 700 000 000"


async def test_public_site_info(api):
    resp = await api.get("/api/site-info")
    assert resp.status_code == 200
    body = resp.json()
    assert "contact_phone" in body and "payment_mode" in body


async def test_settings_require_auth(api):
    resp = await api.get("/api/admin/settings")
    assert resp.status_code == 401


async def test_mark_read_nonexistent_returns_404(admin):
    resp = await admin.put(
        "/api/admin/messages/000000000000000000000001/read",
        json={"read": True},
    )
    assert resp.status_code == 404
