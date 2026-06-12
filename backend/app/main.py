from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.db import init_db
from app.routers.admin_locations import router as admin_locations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = await init_db()
    yield
    client.close()


app = FastAPI(title="Covareli API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(admin_locations_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
