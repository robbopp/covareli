from datetime import datetime

from beanie import PydanticObjectId

from app.models import Booking, BookingStatus, Customer, PriceBreakdown


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
