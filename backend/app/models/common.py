from enum import Enum

from pydantic import BaseModel


class LocalizedStr(BaseModel):
    ro: str = ""
    en: str = ""


class BodyType(str, Enum):
    hatchback = "hatchback"
    sedan = "sedan"
    suv = "suv"
    van = "van"
    wagon = "wagon"


class FuelType(str, Enum):
    petrol = "petrol"
    diesel = "diesel"
    hybrid = "hybrid"
    electric = "electric"


class Transmission(str, Enum):
    manual = "manual"
    automatic = "automatic"


class PriceTier(BaseModel):
    min_days: int
    max_days: int | None = None  # None = no upper bound
    price_per_day: int  # whole RON
