from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.models import Booking, BookingStatus, Car, Location
from app.models.booking import Customer, PriceBreakdown
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def car(db):
    c = Car(
        brand="Dacia", model="Logan", year=2020,
        body_type=BodyType.sedan, fuel=FuelType.petrol,
        transmission=Transmission.manual, seats=5, doors=4,
        price_tiers=[PriceTier(min_days=1, price_per_day=200)],
        slug="dacia-logan-ipn-test",
    )
    await c.insert()
    return c


@pytest_asyncio.fixture
async def loc(db):
    loc_obj = Location(name=LocalizedStr(ro="Aeroport", en="Airport"), fee=0)
    await loc_obj.insert()
    return loc_obj


@pytest_asyncio.fixture
async def pending_booking(db, car, loc):
    booking = Booking(
        car_id=car.id,
        customer=Customer(name="Ion Popescu", email="ion@example.com", phone="0721000000"),
        pickup_at=datetime(2025, 7, 10, 10, 0),
        dropoff_at=datetime(2025, 7, 12, 10, 0),
        pickup_location_id=loc.id,
        dropoff_location_id=loc.id,
        price=PriceBreakdown(days=2, price_per_day=200, car_total=400, pickup_fee=0, dropoff_fee=0, total=400),
        status=BookingStatus.pending_payment,
        netopia_ref="NTP-001",
    )
    await booking.insert()
    return booking


def _ipn_body(order_id: str, ntp_id: str = "NTP-001") -> dict:
    return {"payment": {"ntpID": ntp_id, "orderID": order_id}}


def _status_info(order_id: str, status: int = 3, amount: float = 400.0) -> dict:
    return {"status": status, "order_id": order_id, "amount": amount}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_ipn_paid_status_marks_booking_paid(api, pending_booking):
    order_id = str(pending_booking.id)
    with patch(
        "app.routers.netopia_ipn.get_payment_status",
        new=AsyncMock(return_value=_status_info(order_id, status=3)),
    ), patch(
        "app.routers.netopia_ipn.send_booking_confirmation",
        new=AsyncMock(),
    ), patch(
        "app.routers.netopia_ipn.send_admin_booking_notification",
        new=AsyncMock(),
    ):
        resp = await api.post("/api/netopia/ipn", json=_ipn_body(order_id))

    assert resp.status_code == 200
    assert resp.json() == {"code": "0", "message": "ok"}

    refreshed = await Booking.get(pending_booking.id)
    assert refreshed.status == BookingStatus.paid


async def test_ipn_paid_status_sends_emails(api, pending_booking):
    order_id = str(pending_booking.id)
    mock_confirm = AsyncMock()
    mock_admin = AsyncMock()
    with patch(
        "app.routers.netopia_ipn.get_payment_status",
        new=AsyncMock(return_value=_status_info(order_id, status=3)),
    ), patch(
        "app.routers.netopia_ipn.send_booking_confirmation",
        new=mock_confirm,
    ), patch(
        "app.routers.netopia_ipn.send_admin_booking_notification",
        new=mock_admin,
    ):
        await api.post("/api/netopia/ipn", json=_ipn_body(order_id))

    mock_confirm.assert_awaited_once()
    mock_admin.assert_awaited_once()


async def test_ipn_idempotent_no_emails_for_already_paid(api, pending_booking):
    """Second IPN when booking is already paid must not send emails again."""
    # First — mark booking as paid directly
    pending_booking.status = BookingStatus.paid
    await pending_booking.save()

    order_id = str(pending_booking.id)
    mock_confirm = AsyncMock()
    mock_admin = AsyncMock()
    with patch(
        "app.routers.netopia_ipn.get_payment_status",
        new=AsyncMock(return_value=_status_info(order_id, status=3)),
    ), patch(
        "app.routers.netopia_ipn.send_booking_confirmation",
        new=mock_confirm,
    ), patch(
        "app.routers.netopia_ipn.send_admin_booking_notification",
        new=mock_admin,
    ):
        resp = await api.post("/api/netopia/ipn", json=_ipn_body(order_id))

    assert resp.status_code == 200
    mock_confirm.assert_not_awaited()
    mock_admin.assert_not_awaited()


async def test_ipn_unpaid_status_marks_booking_cancelled(api, pending_booking):
    order_id = str(pending_booking.id)
    with patch(
        "app.routers.netopia_ipn.get_payment_status",
        new=AsyncMock(return_value=_status_info(order_id, status=2)),
    ), patch(
        "app.routers.netopia_ipn.send_booking_confirmation",
        new=AsyncMock(),
    ), patch(
        "app.routers.netopia_ipn.send_admin_booking_notification",
        new=AsyncMock(),
    ):
        resp = await api.post("/api/netopia/ipn", json=_ipn_body(order_id))

    assert resp.status_code == 200
    refreshed = await Booking.get(pending_booking.id)
    assert refreshed.status == BookingStatus.cancelled


async def test_ipn_order_id_mismatch_booking_unchanged(api, pending_booking):
    order_id = str(pending_booking.id)
    # Status API returns a different orderID than the IPN body
    with patch(
        "app.routers.netopia_ipn.get_payment_status",
        new=AsyncMock(return_value=_status_info("000000000000000000000099", status=3)),
    ), patch(
        "app.routers.netopia_ipn.send_booking_confirmation",
        new=AsyncMock(),
    ), patch(
        "app.routers.netopia_ipn.send_admin_booking_notification",
        new=AsyncMock(),
    ):
        resp = await api.post("/api/netopia/ipn", json=_ipn_body(order_id))

    assert resp.status_code == 200
    refreshed = await Booking.get(pending_booking.id)
    assert refreshed.status == BookingStatus.pending_payment


async def test_ipn_unknown_booking_returns_200(api, db):
    unknown_id = "000000000000000000000099"
    with patch(
        "app.routers.netopia_ipn.get_payment_status",
        new=AsyncMock(return_value=_status_info(unknown_id, status=3)),
    ):
        resp = await api.post("/api/netopia/ipn", json=_ipn_body(unknown_id))

    assert resp.status_code == 200
    assert resp.json() == {"code": "0", "message": "ok"}


async def test_ipn_malformed_body_returns_200(api, db):
    resp = await api.post(
        "/api/netopia/ipn",
        content=b"not-json-at-all",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"code": "0", "message": "ok"}
