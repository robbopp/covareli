from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.deps import require_admin
from app.models import ContactMessage

router = APIRouter(
    prefix="/api/admin/messages",
    tags=["admin:messages"],
    dependencies=[Depends(require_admin)],
)


def serialize(msg: ContactMessage) -> dict:
    return {
        "id": str(msg.id),
        "name": msg.name,
        "email": msg.email,
        "phone": msg.phone,
        "message": msg.message,
        "read": msg.read,
        "created_at": msg.created_at.isoformat(),
    }


class ReadBody(BaseModel):
    read: bool


@router.get("")
async def list_messages():
    msgs = await ContactMessage.find_all().sort("-created_at").to_list()
    return [serialize(m) for m in msgs]


@router.put("/{message_id}/read")
async def mark_read(message_id: PydanticObjectId, body: ReadBody):
    msg = await ContactMessage.get(message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.read = body.read
    await msg.save()
    return serialize(msg)
