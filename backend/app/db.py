from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import config
from app.models import ALL_MODELS


async def init_db() -> AsyncIOMotorClient:
    client = AsyncIOMotorClient(config.mongo_url)
    await init_beanie(database=client[config.mongo_db], document_models=ALL_MODELS)
    return client
