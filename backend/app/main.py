from fastapi import FastAPI

app = FastAPI(title="Covareli API")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
