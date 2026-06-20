from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.config import config
from app.db import init_db
from app.routers.admin_cars import router as admin_cars_router
from app.routers.admin_locations import router as admin_locations_router
from app.routers.admin_messages import router as admin_messages_router
from app.routers.admin_settings import router as admin_settings_router
from app.routers.admin_bookings import router as admin_bookings_router
from app.routers.bookings import router as bookings_router
from app.routers.public import router as public_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = await init_db()
    yield
    client.close()


app = FastAPI(title="Covareli API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(admin_locations_router)
app.include_router(admin_cars_router)
app.include_router(admin_messages_router)
app.include_router(admin_settings_router)
app.include_router(public_router)
app.include_router(bookings_router)
app.include_router(admin_bookings_router)

Path(config.media_dir).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=config.media_dir), name="media")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
