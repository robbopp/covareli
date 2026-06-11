from beanie import Document
from pydantic import Field

from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission


class Car(Document):
    brand: str
    model: str
    year: int
    body_type: BodyType
    fuel: FuelType
    transmission: Transmission
    seats: int
    doors: int
    engine: str = ""
    images: list[str] = Field(default_factory=list)  # filenames, ordered
    description: LocalizedStr = Field(default_factory=LocalizedStr)
    features: list[LocalizedStr] = Field(default_factory=list)
    price_tiers: list[PriceTier] = Field(default_factory=list)
    deposit_info: LocalizedStr = Field(default_factory=LocalizedStr)
    active: bool = True
    slug: str

    class Settings:
        name = "cars"
