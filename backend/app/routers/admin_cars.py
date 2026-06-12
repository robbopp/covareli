from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.auth.deps import require_admin
from app.models import Car
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission
from app.slugs import unique_car_slug

router = APIRouter(
    prefix="/api/admin/cars",
    tags=["admin:cars"],
    dependencies=[Depends(require_admin)],
)


class CarBody(BaseModel):
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    year: int = Field(ge=1990, le=2100)
    body_type: BodyType
    fuel: FuelType
    transmission: Transmission
    seats: int = Field(ge=1, le=9)
    doors: int = Field(ge=2, le=6)
    engine: str = ""
    description: LocalizedStr = Field(default_factory=LocalizedStr)
    features: list[LocalizedStr] = Field(default_factory=list)
    price_tiers: list[PriceTier] = Field(min_length=1)
    deposit_info: LocalizedStr = Field(default_factory=LocalizedStr)
    active: bool = True


def serialize(car: Car) -> dict:
    data = car.model_dump(exclude={"id", "revision_id"})
    data["id"] = str(car.id)
    return data


async def get_or_404(car_id: PydanticObjectId) -> Car:
    car = await Car.get(car_id)
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.get("")
async def list_cars():
    cars = await Car.find_all().sort("+brand", "+model").to_list()
    return [serialize(c) for c in cars]


@router.post("", status_code=201)
async def create_car(body: CarBody):
    slug = await unique_car_slug(f"{body.brand} {body.model} {body.year}")
    car = Car(**body.model_dump(), slug=slug)
    await car.insert()
    return serialize(car)


@router.put("/{car_id}")
async def update_car(car_id: PydanticObjectId, body: CarBody):
    car = await get_or_404(car_id)
    for key, value in body:
        setattr(car, key, value)
    await car.save()
    return serialize(car)


@router.delete("/{car_id}", status_code=204)
async def delete_car(car_id: PydanticObjectId):
    car = await get_or_404(car_id)
    await car.delete()
    return Response(status_code=204)
