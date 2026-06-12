from enum import Enum

from pydantic import BaseModel, Field, model_validator


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
    min_days: int = Field(ge=1)
    max_days: int | None = Field(default=None, ge=1)
    price_per_day: int = Field(ge=1)  # whole RON

    @model_validator(mode="after")
    def max_days_gte_min_days(self) -> "PriceTier":
        if self.max_days is not None and self.max_days < self.min_days:
            raise ValueError("max_days must be >= min_days")
        return self
