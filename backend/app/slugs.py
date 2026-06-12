import re
import unicodedata


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return text.strip("-")


async def unique_car_slug(base_text: str) -> str:
    from app.models import Car

    base = slugify(base_text)
    slug = base
    counter = 2
    while await Car.find_one(Car.slug == slug) is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug
