from datetime import datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth.deps import require_admin
from app.models import Booking, BookingStatus

router = APIRouter(
    prefix="/api/admin/bookings",
    tags=["admin-bookings"],
    dependencies=[Depends(require_admin)],
)

VALID_TRANSITIONS: dict[BookingStatus, list[BookingStatus]] = {
    BookingStatus.pending_payment: [BookingStatus.cancelled],
    BookingStatus.paid: [BookingStatus.confirmed, BookingStatus.cancelled],
    BookingStatus.confirmed: [BookingStatus.completed, BookingStatus.cancelled],
}


def serialize_booking(b: Booking) -> dict:
    data = b.model_dump(exclude={"id", "revision_id"})
    data["id"] = str(b.id)
    data["car_id"] = str(b.car_id)
    data["pickup_location_id"] = str(b.pickup_location_id)
    data["dropoff_location_id"] = str(b.dropoff_location_id)
    return data


@router.get("")
async def list_bookings(
    status: BookingStatus | None = None,
    car_id: str | None = None,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
):
    query = Booking.find()
    if status is not None:
        query = query.find(Booking.status == status)
    if car_id is not None:
        try:
            query = query.find(Booking.car_id == PydanticObjectId(car_id))
        except Exception:
            raise HTTPException(status_code=422, detail="invalid car_id")
    if from_ is not None:
        query = query.find(Booking.pickup_at >= from_)
    if to is not None:
        query = query.find(Booking.pickup_at <= to)
    bookings = await query.sort("-created_at").to_list()
    return [serialize_booking(b) for b in bookings]


@router.get("/{booking_id}")
async def get_booking(booking_id: PydanticObjectId):
    booking = await Booking.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return serialize_booking(booking)


class TransitionBody(BaseModel):
    status: BookingStatus
    admin_notes: str = ""


@router.patch("/{booking_id}")
async def update_booking_status(booking_id: PydanticObjectId, body: TransitionBody):
    booking = await Booking.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    allowed = VALID_TRANSITIONS.get(booking.status, [])
    if body.status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot transition from '{booking.status}' to '{body.status}'",
        )

    booking.status = body.status
    if body.admin_notes:
        booking.admin_notes = body.admin_notes
    await booking.save()
    return serialize_booking(booking)
