import pytest
import pytest_asyncio

from app.auth.security import hash_password
from app.models import AdminUser, Car
from app.models.common import PriceTier
from app.slugs import slugify

CAR = {
    "brand": "Audi",
    "model": "A6 AllRoad",
    "year": 2022,
    "body_type": "wagon",
    "fuel": "diesel",
    "transmission": "automatic",
    "seats": 5,
    "doors": 5,
    "engine": "3.0 TDI",
    "description": {"ro": "Break premium", "en": "Premium wagon"},
    "features": [{"ro": "Navigație", "en": "Navigation"}],
    "price_tiers": [
        {"min_days": 1, "max_days": 2, "price_per_day": 350},
        {"min_days": 3, "max_days": None, "price_per_day": 300},
    ],
    "deposit_info": {"ro": "Garanție 1000 lei", "en": "1000 RON deposit"},
    "active": True,
}


def test_slugify():
    assert slugify("Audi A6 AllRoad 2022") == "audi-a6-allroad-2022"
    assert slugify("Škoda Octavia") == "skoda-octavia"


@pytest_asyncio.fixture
async def admin(api):
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    return api


async def test_create_car_generates_unique_slug(admin):
    resp = await admin.post("/api/admin/cars", json=CAR)
    assert resp.status_code == 201
    assert resp.json()["slug"] == "audi-a6-allroad-2022"

    resp = await admin.post("/api/admin/cars", json=CAR)
    assert resp.status_code == 201
    assert resp.json()["slug"] == "audi-a6-allroad-2022-2"


async def test_car_crud_cycle(admin):
    created = (await admin.post("/api/admin/cars", json=CAR)).json()
    car_id = created["id"]

    resp = await admin.get("/api/admin/cars")
    assert len(resp.json()) == 1

    resp = await admin.put(f"/api/admin/cars/{car_id}", json={**CAR, "seats": 4})
    assert resp.status_code == 200
    assert resp.json()["seats"] == 4
    # slug unchanged on update
    assert resp.json()["slug"] == "audi-a6-allroad-2022"

    resp = await admin.delete(f"/api/admin/cars/{car_id}")
    assert resp.status_code == 204
    assert await Car.find_all().count() == 0


async def test_invalid_price_tiers_rejected(admin):
    bad = {**CAR, "price_tiers": []}
    resp = await admin.post("/api/admin/cars", json=bad)
    assert resp.status_code == 422


async def test_update_nonexistent_car_returns_404(admin):
    resp = await admin.put("/api/admin/cars/64b000000000000000000000", json=CAR)
    assert resp.status_code == 404


async def test_delete_nonexistent_car_returns_404(admin):
    resp = await admin.delete("/api/admin/cars/64b000000000000000000000")
    assert resp.status_code == 404


def test_price_tier_min_days_ge_1():
    with pytest.raises(Exception):
        PriceTier(min_days=0, price_per_day=100)


def test_price_tier_price_per_day_ge_1():
    with pytest.raises(Exception):
        PriceTier(min_days=1, price_per_day=0)


def test_price_tier_max_days_gte_min_days():
    with pytest.raises(Exception):
        PriceTier(min_days=5, max_days=3, price_per_day=100)


def test_price_tier_valid_open_ended():
    tier = PriceTier(min_days=3, max_days=None, price_per_day=200)
    assert tier.max_days is None


def test_price_tier_valid_bounded():
    tier = PriceTier(min_days=1, max_days=3, price_per_day=300)
    assert tier.max_days == 3


async def test_invalid_price_tier_via_api_returns_422(admin):
    bad = {**CAR, "price_tiers": [{"min_days": 5, "max_days": 2, "price_per_day": 100}]}
    resp = await admin.post("/api/admin/cars", json=bad)
    assert resp.status_code == 422
