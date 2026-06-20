from datetime import datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.availability import car_is_available
from app.models import Booking, BookingStatus, Car, Customer, Location
from app.pricing import quote_total

router = APIRouter(prefix="/api", tags=["bookings"])


class BookingRequest(BaseModel):
    car_id: str
    customer_name: str = Field(min_length=2, max_length=200)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=4, max_length=30)
    pickup_at: datetime
    dropoff_at: datetime
    pickup_location_id: str
    dropoff_location_id: str


@router.post("/bookings", status_code=201)
async def create_booking(body: BookingRequest):
    pickup_dt = body.pickup_at
    dropoff_dt = body.dropoff_at

    if dropoff_dt <= pickup_dt:
        raise HTTPException(status_code=422, detail="'dropoff_at' must be after 'pickup_at'")

    try:
        car_oid = PydanticObjectId(body.car_id)
    except Exception:
        raise HTTPException(status_code=422, detail="invalid car_id")

    car = await Car.find_one(Car.id == car_oid, Car.active == True)  # noqa: E712
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")

    try:
        pickup_loc_oid = PydanticObjectId(body.pickup_location_id)
        dropoff_loc_oid = PydanticObjectId(body.dropoff_location_id)
    except Exception:
        raise HTTPException(status_code=422, detail="invalid location_id")

    pickup_loc = await Location.find_one(Location.id == pickup_loc_oid, Location.active == True)  # noqa: E712
    dropoff_loc = await Location.find_one(Location.id == dropoff_loc_oid, Location.active == True)  # noqa: E712
    if pickup_loc is None or dropoff_loc is None:
        raise HTTPException(status_code=404, detail="Location not found")

    available = await car_is_available(car_oid, pickup_dt, dropoff_dt)
    if not available:
        raise HTTPException(status_code=409, detail="Car not available for selected dates")

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
async def booking_status(booking_id: PydanticObjectId):
    booking = await Booking.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"status": booking.status, "booking_id": str(booking_id)}
