from beanie import Document


class AdminUser(Document):
    email: str
    password_hash: str

    class Settings:
        name = "admin_users"
