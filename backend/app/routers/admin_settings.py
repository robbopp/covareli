from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.deps import require_admin
from app.models import SiteSettings
from app.models.settings_doc import PaymentMode

router = APIRouter(
    prefix="/api/admin/settings",
    tags=["admin:settings"],
    dependencies=[Depends(require_admin)],
)


class SettingsBody(BaseModel):
    payment_mode: PaymentMode
    advance_value: int = Field(ge=0)
    contact_phone: str
    contact_email: str
    contact_address: str


def serialize(s: SiteSettings) -> dict:
    return {
        "payment_mode": s.payment_mode,
        "advance_value": s.advance_value,
        "contact_phone": s.contact_phone,
        "contact_email": s.contact_email,
        "contact_address": s.contact_address,
    }


@router.get("")
async def get_settings():
    return serialize(await SiteSettings.get_singleton())


@router.put("")
async def update_settings(body: SettingsBody):
    s = await SiteSettings.get_singleton()
    for key, value in body.model_dump().items():
        setattr(s, key, value)
    await s.save()
    return serialize(s)
