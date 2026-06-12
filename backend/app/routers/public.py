from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from app.availability import booked_ranges as get_booked_ranges
from app.availability import car_is_available
from app.models import Car, ContactMessage, Location, SiteSettings
from app.models.common import BodyType, FuelType, Transmission

router = APIRouter(prefix="/api", tags=["public"])


def serialize_car(car: Car) -> dict:
    data = car.model_dump(exclude={"id", "revision_id"})
    data["id"] = str(car.id)
    data["price_from"] = min(t.price_per_day for t in car.price_tiers)
    return data


@router.get("/cars")
async def list_cars(
    body_type: BodyType | None = None,
    fuel: FuelType | None = None,
    transmission: Transmission | None = None,
    seats_min: int | None = None,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
):
    query = Car.find(Car.active == True)  # noqa: E712
    if body_type is not None:
        query = query.find(Car.body_type == body_type)
    if fuel is not None:
        query = query.find(Car.fuel == fuel)
    if transmission is not None:
        query = query.find(Car.transmission == transmission)
    if seats_min is not None:
        query = query.find(Car.seats >= seats_min)
    cars = await query.sort("+brand", "+model").to_list()

    if (from_ is None) != (to is None):
        raise HTTPException(status_code=422, detail="'from' and 'to' must both be provided together")

    if from_ is not None and to is not None:
        if to <= from_:
            raise HTTPException(status_code=422, detail="'to' must be after 'from'")
        available = []
        for car in cars:
            if await car_is_available(car.id, from_, to):
                available.append(car)
        cars = available

    return [serialize_car(c) for c in cars]


async def active_car_by_slug(slug: str) -> Car:
    car = await Car.find_one(Car.slug == slug, Car.active == True)  # noqa: E712
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.get("/cars/{slug}")
async def car_detail(slug: str):
    return serialize_car(await active_car_by_slug(slug))


@router.get("/cars/{slug}/booked-ranges")
async def car_booked_ranges(slug: str):
    car = await active_car_by_slug(slug)
    ranges = await get_booked_ranges(car.id)
    return [
        {"start": start.isoformat(), "end": end.isoformat()}
        for start, end in ranges
    ]


@router.get("/locations")
async def list_locations():
    locs = await Location.find(Location.active == True).sort("+sort_order").to_list()  # noqa: E712
    return [
        {"id": str(loc.id), "name": loc.name.model_dump(), "address": loc.address, "fee": loc.fee}
        for loc in locs
    ]


class ContactBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str = Field(default="", max_length=30)
    message: str = Field(min_length=1, max_length=5000)


@router.post("/contact", status_code=201)
async def submit_contact(body: ContactBody):
    msg = ContactMessage(**body.model_dump())
    await msg.insert()
    return {"ok": True}


@router.get("/site-info")
async def site_info():
    s = await SiteSettings.get_singleton()
    return {
        "payment_mode": s.payment_mode,
        "advance_value": s.advance_value,
        "contact_phone": s.contact_phone,
        "contact_email": s.contact_email,
        "contact_address": s.contact_address,
    }
