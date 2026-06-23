from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.models import Booking, BookingStatus, Car, Location
from app.models.booking import Customer, PriceBreakdown
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission

FAKE_NETOPIA = {"payment_url": "https://sandbox.netopia.com/pay/test", "ntp_id": "NTP-TEST"}


@pytest.fixture(autouse=True)
def mock_init_payment():
    with patch(
        "app.routers.bookings.init_payment",
        new_callable=AsyncMock,
        return_value=FAKE_NETOPIA,
    ) as m:
        yield m


@pytest_asyncio.fixture
async def car(db):
    c = Car(
        brand="Dacia", model="Logan", year=2020,
        body_type=BodyType.sedan, fuel=FuelType.petrol,
        transmission=Transmission.manual, seats=5, doors=4,
        price_tiers=[
            PriceTier(min_days=1, max_days=2, price_per_day=200),
            PriceTier(min_days=3, price_per_day=170),
        ],
        slug="dacia-logan-test-booking",
    )
    await c.insert()
    return c


@pytest_asyncio.fixture
async def loc(db):
    loc_obj = Location(name=LocalizedStr(ro="Aeroport", en="Airport"), fee=50)
    await loc_obj.insert()
    return loc_obj


async def test_create_booking_happy_path(api, car, loc):
    body = {
        "car_id": str(car.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-10T10:00:00",
        "dropoff_at": "2025-07-12T10:00:00",  # 2 days
        "pickup_location_id": str(loc.id),
        "dropoff_location_id": str(loc.id),
    }
    resp = await api.post("/api/bookings", json=body)

    assert resp.status_code == 201
    data = resp.json()
    assert "booking_id" in data
    assert "payment_url" in data
    assert data["payment_url"] == FAKE_NETOPIA["payment_url"]
    assert "price" in data
    assert data["price"]["days"] == 2
    assert data["price"]["price_per_day"] == 200
    assert data["price"]["pickup_fee"] == 50
    assert data["price"]["dropoff_fee"] == 50
    assert data["price"]["total"] == 500  # 2*200 + 50 + 50

    from beanie import PydanticObjectId
    booking = await Booking.get(PydanticObjectId(data["booking_id"]))
    assert booking is not None
    assert booking.status == BookingStatus.pending_payment
    assert booking.customer.name == "Ion Popescu"
    assert booking.customer.email == "ion@example.com"
    assert booking.netopia_ref == FAKE_NETOPIA["ntp_id"]


async def test_create_booking_car_not_found(api, db, loc):
    body = {
        "car_id": "000000000000000000000001",
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-10T10:00:00",
        "dropoff_at": "2025-07-12T10:00:00",
        "pickup_location_id": "000000000000000000000002",
        "dropoff_location_id": "000000000000000000000002",
    }
    resp = await api.post("/api/bookings", json=body)
    assert resp.status_code == 404


async def test_create_booking_location_not_found(api, car, db):
    body = {
        "car_id": str(car.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-10T10:00:00",
        "dropoff_at": "2025-07-12T10:00:00",
        "pickup_location_id": "000000000000000000000002",
        "dropoff_location_id": "000000000000000000000002",
    }
    resp = await api.post("/api/bookings", json=body)
    assert resp.status_code == 404


async def test_create_booking_dropoff_before_pickup(api, car, loc):
    body = {
        "car_id": str(car.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-12T10:00:00",
        "dropoff_at": "2025-07-10T10:00:00",
        "pickup_location_id": str(loc.id),
        "dropoff_location_id": str(loc.id),
    }
    resp = await api.post("/api/bookings", json=body)
    assert resp.status_code == 422


async def test_create_booking_unavailable_car(api, car, loc):
    existing = Booking(
        car_id=car.id,
        customer=Customer(name="Alt Client", email="alt@x.com", phone="0700"),
        pickup_at=datetime(2025, 7, 10, 10, 0),
        dropoff_at=datetime(2025, 7, 12, 10, 0),
        pickup_location_id=loc.id,
        dropoff_location_id=loc.id,
        price=PriceBreakdown(days=2, price_per_day=200, car_total=400, pickup_fee=50, dropoff_fee=50, total=500),
        status=BookingStatus.paid,
    )
    await existing.insert()

    body = {
        "car_id": str(car.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-11T10:00:00",
        "dropoff_at": "2025-07-13T10:00:00",
        "pickup_location_id": str(loc.id),
        "dropoff_location_id": str(loc.id),
    }
    resp = await api.post("/api/bookings", json=body)
    assert resp.status_code == 409


async def test_create_booking_inactive_car_not_found(api, db, loc):
    inactive = Car(
        brand="Ford", model="Focus", year=2019,
        body_type=BodyType.hatchback, fuel=FuelType.petrol,
        transmission=Transmission.manual, seats=5, doors=4,
        price_tiers=[PriceTier(min_days=1, price_per_day=150)],
        slug="ford-focus-inactive",
        active=False,
    )
    await inactive.insert()

    body = {
        "car_id": str(inactive.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-10T10:00:00",
        "dropoff_at": "2025-07-12T10:00:00",
        "pickup_location_id": str(loc.id),
        "dropoff_location_id": str(loc.id),
    }
    resp = await api.post("/api/bookings", json=body)
    assert resp.status_code == 404


async def test_booking_status_returns_current_status(api, car, loc):
    booking = Booking(
        car_id=car.id,
        customer=Customer(name="Ion Pop", email="ion@x.com", phone="0721"),
        pickup_at=datetime(2025, 7, 10, 10, 0),
        dropoff_at=datetime(2025, 7, 12, 10, 0),
        pickup_location_id=loc.id,
        dropoff_location_id=loc.id,
        price=PriceBreakdown(days=2, price_per_day=200, car_total=400, pickup_fee=0, dropoff_fee=0, total=400),
        status=BookingStatus.paid,
    )
    await booking.insert()

    resp = await api.get(f"/api/bookings/{booking.id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "paid"
    assert data["booking_id"] == str(booking.id)


async def test_booking_status_not_found(api, db):
    resp = await api.get("/api/bookings/000000000000000000000099/status")
    assert resp.status_code == 404


async def test_create_booking_netopia_failure_returns_502(api, car, loc, mock_init_payment):
    mock_init_payment.side_effect = Exception("Netopia unreachable")
    body = {
        "car_id": str(car.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-10T10:00:00",
        "dropoff_at": "2025-07-12T10:00:00",
        "pickup_location_id": str(loc.id),
        "dropoff_location_id": str(loc.id),
    }
    resp = await api.post("/api/bookings", json=body)
    assert resp.status_code == 502
