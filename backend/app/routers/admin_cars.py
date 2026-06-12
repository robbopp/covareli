import shutil

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from app.auth.deps import require_admin
from app.images import car_media_dir, delete_car_image, save_car_image
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
    engine: str = Field(default="", max_length=100)
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
    for key, value in body.model_dump().items():
        setattr(car, key, value)
    await car.save()
    return serialize(car)


@router.delete("/{car_id}", status_code=204)
async def delete_car(car_id: PydanticObjectId):
    car = await get_or_404(car_id)
    shutil.rmtree(car_media_dir(str(car.id)), ignore_errors=True)
    await car.delete()
    return Response(status_code=204)


class ImageOrderBody(BaseModel):
    images: list[str]


@router.post("/{car_id}/images", status_code=201)
async def upload_image(car_id: PydanticObjectId, file: UploadFile):
    car = await get_or_404(car_id)
    name = await save_car_image(str(car.id), file)
    car.images.append(name)
    await car.save()
    return {"name": name, "images": car.images}


@router.put("/{car_id}/images/order")
async def reorder_images(car_id: PydanticObjectId, body: ImageOrderBody):
    car = await get_or_404(car_id)
    if sorted(body.images) != sorted(car.images):
        raise HTTPException(status_code=400, detail="Image list does not match car images")
    car.images = body.images
    await car.save()
    return {"images": car.images}


@router.delete("/{car_id}/images/{name}")
async def delete_image(car_id: PydanticObjectId, name: str):
    car = await get_or_404(car_id)
    if name not in car.images:
        raise HTTPException(status_code=404, detail="Image not found")
    delete_car_image(str(car.id), name)
    car.images.remove(name)
    await car.save()
    return {"images": car.images}
