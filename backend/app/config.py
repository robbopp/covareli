from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "covareli"
    jwt_secret: str = "dev-secret-change-me"
    jwt_expires_hours: int = 12
    cookie_secure: bool = False
    media_dir: str = "media"


config = AppConfig()
