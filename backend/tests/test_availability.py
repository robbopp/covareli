from datetime import datetime, timedelta

from beanie import PydanticObjectId

from app.availability import PENDING_HOLD_MINUTES, booked_ranges, car_is_available
from app.models import Booking, BookingStatus, Customer, PriceBreakdown
from app.timeutil import utcnow


def make_booking(car_id, pickup, dropoff, status, created_at=None):
    booking = Booking(
        car_id=car_id,
        customer=Customer(name="Test Client", email="client@test.ro", phone="0700000000"),
        pickup_at=pickup,
        dropoff_at=dropoff,
        pickup_location_id=PydanticObjectId(),
        dropoff_location_id=PydanticObjectId(),
        price=PriceBreakdown(days=1, price_per_day=200, car_total=200, total=200),
        status=status,
    )
    if created_at is not None:
        booking.created_at = created_at
    return booking


async def test_booking_roundtrip(db):
    car_id = PydanticObjectId()
    booking = make_booking(
        car_id, datetime(2026, 7, 1, 10), datetime(2026, 7, 3, 10), BookingStatus.paid
    )
    await booking.insert()
    found = await Booking.find_one(Booking.car_id == car_id)
    assert found is not None
    assert found.status == BookingStatus.paid


async def test_no_bookings_means_available(db):
    assert await car_is_available(
        PydanticObjectId(), datetime(2026, 7, 1, 10), datetime(2026, 7, 5, 10)
    )


async def test_overlapping_paid_booking_blocks(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.paid
    ).insert()
    assert not await car_is_available(
        car_id, datetime(2026, 7, 3, 10), datetime(2026, 7, 6, 10)
    )


async def test_adjacent_booking_does_not_block(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 1, 10), datetime(2026, 7, 3, 10), BookingStatus.confirmed
    ).insert()
    # starts exactly when the other ends
    assert await car_is_available(
        car_id, datetime(2026, 7, 3, 10), datetime(2026, 7, 5, 10)
    )


async def test_cancelled_booking_does_not_block(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.cancelled
    ).insert()
    assert await car_is_available(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10)
    )


async def test_completed_booking_does_not_block(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.completed
    ).insert()
    assert await car_is_available(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10)
    )


async def test_fresh_pending_payment_blocks(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10),
        BookingStatus.pending_payment, created_at=utcnow(),
    ).insert()
    assert not await car_is_available(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10)
    )


async def test_expired_pending_payment_does_not_block(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10),
        BookingStatus.pending_payment, created_at=utcnow() - timedelta(minutes=PENDING_HOLD_MINUTES + 1),
    ).insert()
    assert await car_is_available(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10)
    )


async def test_booked_ranges_returns_blocking_intervals_only(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.paid
    ).insert()
    await make_booking(
        car_id, datetime(2026, 7, 10, 10), datetime(2026, 7, 12, 10), BookingStatus.cancelled
    ).insert()
    ranges = await booked_ranges(car_id)
    assert ranges == [(datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10))]
