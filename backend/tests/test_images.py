import io

import pytest
import pytest_asyncio
from PIL import Image

from app.auth.security import hash_password
from app.config import config
from app.models import AdminUser

from .test_cars_admin import CAR


@pytest_asyncio.fixture
async def admin(api, tmp_path):
    config.media_dir = str(tmp_path)
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    return api


def png_bytes(width=2000, height=1200) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(120, 30, 30)).save(buf, format="PNG")
    return buf.getvalue()


async def create_car(admin) -> str:
    resp = await admin.post("/api/admin/cars", json=CAR)
    return resp.json()["id"]


async def test_upload_creates_variants_and_updates_car(admin, tmp_path):
    car_id = await create_car(admin)
    resp = await admin.post(
        f"/api/admin/cars/{car_id}/images",
        files={"file": ("photo.png", png_bytes(), "image/png")},
    )
    assert resp.status_code == 201
    name = resp.json()["name"]
    card = tmp_path / "cars" / car_id / f"{name}_card.webp"
    full = tmp_path / "cars" / car_id / f"{name}_full.webp"
    assert card.exists() and full.exists()
    assert Image.open(card).width == 640
    assert Image.open(full).width == 1600

    car = (await admin.get("/api/admin/cars")).json()[0]
    assert car["images"] == [name]


async def test_upload_rejects_non_image(admin):
    car_id = await create_car(admin)
    resp = await admin.post(
        f"/api/admin/cars/{car_id}/images",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 415


async def test_reorder_and_delete_image(admin, tmp_path):
    car_id = await create_car(admin)
    names = []
    for _ in range(2):
        resp = await admin.post(
            f"/api/admin/cars/{car_id}/images",
            files={"file": ("p.png", png_bytes(), "image/png")},
        )
        names.append(resp.json()["name"])

    resp = await admin.put(
        f"/api/admin/cars/{car_id}/images/order", json={"images": names[::-1]}
    )
    assert resp.status_code == 200
    assert resp.json()["images"] == names[::-1]

    resp = await admin.delete(f"/api/admin/cars/{car_id}/images/{names[0]}")
    assert resp.status_code == 200
    assert resp.json()["images"] == [names[1]]
    assert not (tmp_path / "cars" / car_id / f"{names[0]}_card.webp").exists()
