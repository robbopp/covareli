from datetime import datetime, timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.logical import And, Or
from beanie.odm.operators.find.comparison import In

from app.models.booking import Booking, BookingStatus
from app.timeutil import to_naive_utc, utcnow

PENDING_HOLD_MINUTES = 30


def _blocking_filter():
    """Filter for bookings that block availability: paid/confirmed, or pending_payment created within the hold window."""
    hold_cutoff = utcnow() - timedelta(minutes=PENDING_HOLD_MINUTES)
    return Or(
        In(Booking.status, [BookingStatus.paid, BookingStatus.confirmed]),
        And(
            Booking.status == BookingStatus.pending_payment,
            Booking.created_at > hold_cutoff,
        ),
    )


async def car_is_available(
    car_id: PydanticObjectId, start: datetime, end: datetime
) -> bool:
    start, end = to_naive_utc(start), to_naive_utc(end)
    count = await Booking.find(
        Booking.car_id == car_id,
        Booking.pickup_at < end,
        Booking.dropoff_at > start,
        _blocking_filter(),
    ).count()
    return count == 0


async def booked_ranges(
    car_id: PydanticObjectId,
) -> list[tuple[datetime, datetime]]:
    bookings = await Booking.find(
        Booking.car_id == car_id, _blocking_filter()
    ).sort("+pickup_at").to_list()
    return [(b.pickup_at, b.dropoff_at) for b in bookings]
