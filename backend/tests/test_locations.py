import pytest_asyncio

from app.auth.security import hash_password
from app.models import AdminUser

LOCATION = {
    "name": {"ro": "Sediu Baciu", "en": "Baciu Office"},
    "address": "Str. Jupiter 1/12, Baciu",
    "fee": 0,
    "active": True,
    "sort_order": 1,
}


@pytest_asyncio.fixture
async def admin(api):
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    resp = await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    assert resp.status_code == 200
    return api


async def test_crud_requires_auth(api):
    resp = await api.post("/api/admin/locations", json=LOCATION)
    assert resp.status_code == 401


async def test_location_crud_cycle(admin):
    resp = await admin.post("/api/admin/locations", json=LOCATION)
    assert resp.status_code == 201
    loc_id = resp.json()["id"]

    resp = await admin.get("/api/admin/locations")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await admin.put(f"/api/admin/locations/{loc_id}", json={**LOCATION, "fee": 50})
    assert resp.status_code == 200
    assert resp.json()["fee"] == 50

    resp = await admin.delete(f"/api/admin/locations/{loc_id}")
    assert resp.status_code == 204

    resp = await admin.get("/api/admin/locations")
    assert resp.json() == []


async def test_update_missing_location_404(admin):
    resp = await admin.put("/api/admin/locations/64b000000000000000000000", json=LOCATION)
    assert resp.status_code == 404
