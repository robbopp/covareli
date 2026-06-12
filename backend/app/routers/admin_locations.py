from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.auth.deps import require_admin
from app.models import Location
from app.models.common import LocalizedStr

router = APIRouter(
    prefix="/api/admin/locations",
    tags=["admin:locations"],
    dependencies=[Depends(require_admin)],
)


class LocationBody(BaseModel):
    name: LocalizedStr
    address: str = ""
    fee: int = Field(default=0, ge=0)
    active: bool = True
    sort_order: int = 0


def serialize(loc: Location) -> dict:
    return {
        "id": str(loc.id),
        "name": loc.name.model_dump(),
        "address": loc.address,
        "fee": loc.fee,
        "active": loc.active,
        "sort_order": loc.sort_order,
    }


async def get_or_404(location_id: PydanticObjectId) -> Location:
    loc = await Location.get(location_id)
    if loc is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc


@router.get("")
async def list_locations():
    locs = await Location.find_all().sort("+sort_order").to_list()
    return [serialize(l) for l in locs]


@router.post("", status_code=201)
async def create_location(body: LocationBody):
    loc = Location(**body.model_dump())
    await loc.insert()
    return serialize(loc)


@router.put("/{location_id}")
async def update_location(location_id: PydanticObjectId, body: LocationBody):
    loc = await get_or_404(location_id)
    for key, value in body:
        setattr(loc, key, value)
    await loc.save()
    return serialize(loc)


@router.delete("/{location_id}", status_code=204)
async def delete_location(location_id: PydanticObjectId):
    loc = await get_or_404(location_id)
    await loc.delete()
    return Response(status_code=204)
