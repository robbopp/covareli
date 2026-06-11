from beanie import Document
from pydantic import Field

from app.models.common import LocalizedStr


class Location(Document):
    name: LocalizedStr
    address: str = ""
    fee: int = 0  # whole RON
    active: bool = True
    sort_order: int = 0

    class Settings:
        name = "locations"
