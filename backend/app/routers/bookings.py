import logging
from datetime import datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.availability import car_is_available
from app.models import Booking, BookingStatus, Car, Customer, Location
from app.pricing import quote_total

router = APIRouter(prefix="/api", tags=["bookings"])
logger = logging.getLogger(__name__)


class BookingRequest(BaseModel):
    car_id: str
    customer_name: str = Field(min_length=2, max_length=200)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=4, max_length=30)
    pickup_at: str
    dropoff_at: str
    pickup_location_id: str
    dropoff_location_id: str


@router.post("/bookings", status_code=201)
async def create_booking(body: BookingRequest):
    try:
        pickup_dt = datetime.fromisoformat(body.pickup_at)
        dropoff_dt = datetime.fromisoformat(body.dropoff_at)
    except ValueError:
        raise HTTPException(422, "Invalid datetime format; use ISO 8601")

    if dropoff_dt <= pickup_dt:
        raise HTTPException(422, "'dropoff_at' must be after 'pickup_at'")

    try:
        car_oid = PydanticObjectId(body.car_id)
    except Exception:
        raise HTTPException(422, "invalid car_id")

    car = await Car.find_one(Car.id == car_oid, Car.active == True)  # noqa: E712
    if car is None:
        raise HTTPException(404, "Car not found")

    try:
        pickup_loc_oid = PydanticObjectId(body.pickup_location_id)
        dropoff_loc_oid = PydanticObjectId(body.dropoff_location_id)
    except Exception:
        raise HTTPException(422, "invalid location_id")

    pickup_loc = await Location.find_one(Location.id == pickup_loc_oid, Location.active == True)  # noqa: E712
    dropoff_loc = await Location.find_one(Location.id == dropoff_loc_oid, Location.active == True)  # noqa: E712
    if pickup_loc is None or dropoff_loc is None:
        raise HTTPException(404, "Location not found")

    available = await car_is_available(car_oid, pickup_dt, dropoff_dt)
    if not available:
        raise HTTPException(409, "Car not available for selected dates")

    price = quote_total(
        car.price_tiers,
        pickup_dt,
        dropoff_dt,
        pickup_fee=pickup_loc.fee,
        dropoff_fee=dropoff_loc.fee,
    )

    booking = Booking(
        car_id=car_oid,
        customer=Customer(
            name=body.customer_name,
            email=body.customer_email,
            phone=body.customer_phone,
        ),
        pickup_at=pickup_dt,
        dropoff_at=dropoff_dt,
        pickup_location_id=pickup_loc_oid,
        dropoff_location_id=dropoff_loc_oid,
        price=price,
    )
    await booking.insert()

    return {
        "booking_id": str(booking.id),
        "price": price.model_dump(),
    }


@router.get("/bookings/{booking_id}/status")
async def booking_status(booking_id: str):
    try:
        oid = PydanticObjectId(booking_id)
    except Exception:
        raise HTTPException(422, "invalid booking_id")
    booking = await Booking.get(oid)
    if booking is None:
        raise HTTPException(404, "Booking not found")
    return {"status": booking.status, "booking_id": booking_id}
