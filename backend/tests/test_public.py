from datetime import datetime

from app.models import Car, Location
from app.models.common import LocalizedStr, PriceTier

from .test_availability import make_booking
from app.models import BookingStatus


def make_car(brand="Dacia", model="Logan", slug="dacia-logan-2023", active=True,
             fuel="petrol", body_type="sedan") -> Car:
    return Car(
        brand=brand, model=model, year=2023, body_type=body_type, fuel=fuel,
        transmission="manual", seats=5, doors=4,
        price_tiers=[
            PriceTier(min_days=1, max_days=2, price_per_day=200),
            PriceTier(min_days=3, max_days=None, price_per_day=180),
        ],
        active=active, slug=slug,
    )


async def test_list_only_active_cars(api):
    await make_car().insert()
    await make_car(slug="hidden-car", active=False).insert()
    resp = await api.get("/api/cars")
    assert resp.status_code == 200
    cars = resp.json()
    assert len(cars) == 1
    assert cars[0]["slug"] == "dacia-logan-2023"
    assert cars[0]["price_from"] == 180


async def test_list_filters_by_fuel(api):
    await make_car().insert()
    await make_car(slug="tesla", fuel="electric").insert()
    resp = await api.get("/api/cars", params={"fuel": "electric"})
    assert [c["slug"] for c in resp.json()] == ["tesla"]


async def test_list_with_dates_excludes_booked_car(api):
    car = make_car()
    await car.insert()
    await make_booking(
        car.id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.paid
    ).insert()
    resp = await api.get("/api/cars", params={
        "from": "2026-07-03T10:00:00", "to": "2026-07-05T10:00:00"
    })
    assert resp.json() == []
    resp = await api.get("/api/cars", params={
        "from": "2026-07-10T10:00:00", "to": "2026-07-12T10:00:00"
    })
    assert len(resp.json()) == 1


async def test_car_detail_by_slug(api):
    await make_car().insert()
    resp = await api.get("/api/cars/dacia-logan-2023")
    assert resp.status_code == 200
    assert resp.json()["brand"] == "Dacia"
    resp = await api.get("/api/cars/missing")
    assert resp.status_code == 404


async def test_inactive_car_detail_404(api):
    await make_car(active=False).insert()
    resp = await api.get("/api/cars/dacia-logan-2023")
    assert resp.status_code == 404


async def test_booked_ranges_endpoint(api):
    car = make_car()
    await car.insert()
    await make_booking(
        car.id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.paid
    ).insert()
    resp = await api.get("/api/cars/dacia-logan-2023/booked-ranges")
    assert resp.status_code == 200
    assert resp.json() == [
        {"start": "2026-07-02T10:00:00", "end": "2026-07-04T10:00:00"}
    ]


async def test_public_locations_active_sorted(api):
    await Location(name=LocalizedStr(ro="Aeroport", en="Airport"), fee=50, sort_order=2).insert()
    await Location(name=LocalizedStr(ro="Sediu", en="Office"), fee=0, sort_order=1).insert()
    await Location(name=LocalizedStr(ro="Ascuns", en="Hidden"), active=False).insert()
    resp = await api.get("/api/locations")
    names = [l["name"]["ro"] for l in resp.json()]
    assert names == ["Sediu", "Aeroport"]
