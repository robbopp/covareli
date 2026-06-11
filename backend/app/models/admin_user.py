from typing import Annotated

from beanie import Document, Indexed


class AdminUser(Document):
    email: Annotated[str, Indexed(unique=True)]
    password_hash: str

    class Settings:
        name = "admin_users"
