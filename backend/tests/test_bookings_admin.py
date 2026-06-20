from datetime import datetime

import pytest_asyncio

from app.auth.security import hash_password
from app.models import AdminUser, Booking, BookingStatus, Car, Location
from app.models.booking import Customer, PriceBreakdown
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission


@pytest_asyncio.fixture
async def admin(api):
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    await api.post("/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"})
    return api


@pytest_asyncio.fixture
async def car(db):
    c = Car(
        brand="Dacia", model="Logan", year=2020,
        body_type=BodyType.sedan, fuel=FuelType.petrol,
        transmission=Transmission.manual, seats=5, doors=4,
        price_tiers=[PriceTier(min_days=1, price_per_day=200)],
        slug="dacia-logan-admin-bk-test",
    )
    await c.insert()
    return c


@pytest_asyncio.fixture
async def loc(db):
    loc_obj = Location(name=LocalizedStr(ro="Cluj", en="Cluj"), fee=0)
    await loc_obj.insert()
    return loc_obj


def make_booking(car, loc, status=BookingStatus.pending_payment):
    return Booking(
        car_id=car.id,
        customer=Customer(name="Ion Pop", email="ion@example.com", phone="0721"),
        pickup_at=datetime(2025, 7, 10, 10, 0),
        dropoff_at=datetime(2025, 7, 12, 10, 0),
        pickup_location_id=loc.id,
        dropoff_location_id=loc.id,
        price=PriceBreakdown(days=2, price_per_day=200, car_total=400, pickup_fee=0, dropoff_fee=0, total=400),
        status=status,
    )


async def test_list_bookings_returns_all(admin, car, loc):
    b1 = make_booking(car, loc, BookingStatus.pending_payment)
    b2 = make_booking(car, loc, BookingStatus.paid)
    await b1.insert()
    await b2.insert()

    resp = await admin.get("/api/admin/bookings")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_list_bookings_filter_by_status(admin, car, loc):
    b1 = make_booking(car, loc, BookingStatus.pending_payment)
    b2 = make_booking(car, loc, BookingStatus.paid)
    await b1.insert()
    await b2.insert()

    resp = await admin.get("/api/admin/bookings?status=paid")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "paid"


async def test_list_bookings_filter_by_car_id(admin, car, loc):
    b = make_booking(car, loc)
    await b.insert()

    resp = await admin.get(f"/api/admin/bookings?car_id={car.id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp2 = await admin.get("/api/admin/bookings?car_id=000000000000000000000001")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0


async def test_list_bookings_ids_are_strings(admin, car, loc):
    b = make_booking(car, loc)
    await b.insert()

    resp = await admin.get("/api/admin/bookings")
    assert resp.status_code == 200
    data = resp.json()[0]
    assert isinstance(data["id"], str)
    assert isinstance(data["car_id"], str)
    assert isinstance(data["pickup_location_id"], str)
    assert isinstance(data["dropoff_location_id"], str)


async def test_get_booking_detail(admin, car, loc):
    b = make_booking(car, loc)
    await b.insert()

    resp = await admin.get(f"/api/admin/bookings/{b.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(b.id)
    assert data["customer"]["name"] == "Ion Pop"
    assert data["price"]["total"] == 400


async def test_get_booking_not_found(admin, db):
    resp = await admin.get("/api/admin/bookings/000000000000000000000099")
    assert resp.status_code == 404


async def test_transition_paid_to_confirmed(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.paid)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "confirmed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"
    updated = await Booking.get(b.id)
    assert updated.status == BookingStatus.confirmed


async def test_transition_paid_to_cancelled_with_notes(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.paid)
    await b.insert()

    resp = await admin.patch(
        f"/api/admin/bookings/{b.id}",
        json={"status": "cancelled", "admin_notes": "Client a anulat"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelled"
    assert data["admin_notes"] == "Client a anulat"


async def test_transition_confirmed_to_completed(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.confirmed)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "completed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_transition_pending_to_cancelled(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.pending_payment)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "cancelled"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


async def test_invalid_transition_paid_to_completed(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.paid)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "completed"})
    assert resp.status_code == 422


async def test_invalid_transition_completed_to_cancelled(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.completed)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "cancelled"})
    assert resp.status_code == 422


async def test_unauthenticated_access_returns_401(api, db):
    resp = await api.get("/api/admin/bookings")
    assert resp.status_code == 401
