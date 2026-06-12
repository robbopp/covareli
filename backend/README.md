# Covareli backend

FastAPI + MongoDB (Beanie). All amounts are integer RON; all datetimes naive UTC.

## Run locally

    docker compose -f ../docker-compose.dev.yml up -d   # MongoDB
    python3 -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    python scripts/seed_admin.py admin@covareli.ro 'your-password'
    uvicorn app.main:app --reload --port 8000

API docs: http://localhost:8000/docs

## Tests

    pytest tests/ -v

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| MONGO_URL | mongodb://localhost:27017 | Mongo connection |
| MONGO_DB | covareli | DB name |
| JWT_SECRET | dev-secret-change-me | sign admin JWTs (change in prod) |
| JWT_EXPIRES_HOURS | 12 | admin session length |
| COOKIE_SECURE | false | set true behind HTTPS |
| MEDIA_DIR | media | car image storage |
