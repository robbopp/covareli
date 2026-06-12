import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

from app.config import config

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024
VARIANTS = {"card": 640, "full": 1600}


def car_media_dir(car_id: str) -> Path:
    return Path(config.media_dir) / "cars" / car_id


async def save_car_image(car_id: str, file: UploadFile) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG or WebP images allowed")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image larger than 10 MB")
    try:
        original = Image.open(io.BytesIO(raw))
        original.load()
    except Exception:
        raise HTTPException(status_code=415, detail="File is not a valid image")

    name = uuid.uuid4().hex
    target_dir = car_media_dir(car_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    for variant, width in VARIANTS.items():
        img = original.convert("RGB")
        if img.width > width:
            height = round(img.height * width / img.width)
            img = img.resize((width, height), Image.LANCZOS)
        img.save(target_dir / f"{name}_{variant}.webp", format="WEBP", quality=80)
    return name


def delete_car_image(car_id: str, name: str) -> None:
    for variant in VARIANTS:
        path = car_media_dir(car_id) / f"{name}_{variant}.webp"
        path.unlink(missing_ok=True)
