from datetime import datetime

from beanie import Document
from pydantic import Field

from app.timeutil import utcnow


class ContactMessage(Document):
    name: str
    email: str
    phone: str = ""
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "contact_messages"
