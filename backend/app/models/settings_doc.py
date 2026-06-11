from enum import Enum

from beanie import Document


class PaymentMode(str, Enum):
    full = "full"
    advance_percent = "advance_percent"  # reserved, not used in v1 UI
    fixed_deposit = "fixed_deposit"      # reserved, not used in v1 UI


class SiteSettings(Document):
    payment_mode: PaymentMode = PaymentMode.full
    advance_value: int = 0  # percent or RON depending on mode
    contact_phone: str = "+40 749 323 172"
    contact_email: str = "office@covareli.ro"
    contact_address: str = "Str. Jupiter, nr. 1/12, Baciu, Cluj"

    class Settings:
        name = "settings"

    @classmethod
    async def get_singleton(cls) -> "SiteSettings":
        existing = await cls.find_one({})
        if existing:
            return existing
        created = cls()
        await created.insert()
        return created
