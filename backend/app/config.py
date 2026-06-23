import warnings

from pydantic import model_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "covareli"
    jwt_secret: str = "dev-secret-change-me"
    jwt_expires_hours: int = 12
    cookie_secure: bool = False
    media_dir: str = "media"

    # Netopia Payments v2
    netopia_signature: str = ""
    netopia_api_key: str = ""
    netopia_sandbox: bool = True

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@covareli.ro"

    # Public URLs (used in Netopia redirect + IPN URLs — set when Netopia is integrated)
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    cors_origins: list[str] = ["http://localhost:3000"]

    @model_validator(mode="after")
    def _warn_short_jwt_secret(self):
        if len(self.jwt_secret.encode()) < 32:
            warnings.warn(
                "jwt_secret is shorter than 32 bytes; set a 32+ byte JWT_SECRET before production deploy."
            )
        return self


config = AppConfig()
