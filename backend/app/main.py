from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Covareli API", lifespan=lifespan)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
