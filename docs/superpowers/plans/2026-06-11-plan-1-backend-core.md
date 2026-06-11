# Covareli Backend Core — Implementation Plan (Plan 1 of 5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI + MongoDB backend core: data models, pricing and availability logic, admin auth, CRUD APIs for cars/locations/messages/settings, image upload, and the public read API.

**Architecture:** Single FastAPI app (Python 3.12) using Beanie ODM over MongoDB. Pure business logic (pricing, availability) lives in standalone modules tested first. Routers are thin: validation + DB calls. Admin routes guarded by a JWT-in-httpOnly-cookie dependency. Car images stored on disk, resized at upload with Pillow, served as static files. Bookings/payments come in Plan 2; this plan only defines the Booking model and availability rules they will use.

**Tech Stack:** FastAPI, Beanie (Motor), MongoDB, PyJWT, bcrypt, Pillow, pytest + pytest-asyncio + httpx (ASGITransport) + mongomock-motor for tests.

**Spec:** `docs/superpowers/specs/2026-06-11-covareli-rebuild-design.md`

**Conventions used throughout:**
- All datetimes are **naive UTC** (Mongo stores naive UTC; inputs with timezone offsets are normalized via `to_naive_utc`).
- All money amounts are **integer RON (lei)**.
- API base path is `/api`; admin-only routes live under `/api/admin/...`.
- Commit messages in English, no Co-Authored-By lines.
- Run all backend commands from `backend/` with the venv activated.

---

## File Structure

```
covareli/
  .gitignore
  backend/
    requirements.txt
    pytest.ini
    app/
      __init__.py
      config.py            # env settings (pydantic-settings)
      main.py              # app factory, lifespan, router mounting, /media static
      db.py                # Mongo client + init_beanie + ALL_MODELS
      timeutil.py          # to_naive_utc
      pricing.py           # rental_days, price_per_day, quote_total
      availability.py      # car_is_available, booked_ranges
      slugs.py             # slugify + unique slug
      models/
        __init__.py        # re-exports + ALL_MODELS
        common.py          # LocalizedStr, PriceTier, enums
        car.py
        location.py
        booking.py
        contact_message.py
        settings_doc.py
        admin_user.py
      auth/
        __init__.py
        security.py        # bcrypt hash/verify, JWT encode/decode
        deps.py            # require_admin dependency
        routes.py          # login/logout/me/change-password (+ naive rate limit)
      images.py            # validate, resize, save car images
      routers/
        admin_cars.py
        admin_locations.py
        admin_messages.py
        admin_settings.py
        public.py
    scripts/
      seed_admin.py
    tests/
      conftest.py
      test_health.py
      test_pricing.py
      test_availability.py
      test_auth.py
      test_locations.py
      test_cars_admin.py
      test_images.py
      test_public.py
      test_contact_and_settings.py
  docker-compose.dev.yml   # mongo for local dev
```

---

### Task 1: Project scaffolding, health endpoint, test harness

**Files:**
- Create: `.gitignore`, `backend/requirements.txt`, `backend/pytest.ini`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/tests/conftest.py` (minimal), `backend/tests/test_health.py`, `docker-compose.dev.yml`

- [ ] **Step 1: Create `.gitignore`**

```gitignore
__pycache__/
*.pyc
.venv/
venv/
node_modules/
.next/
.env
media/
.DS_Store
.pytest_cache/
```

- [ ] **Step 2: Create `backend/requirements.txt`**

```
fastapi>=0.115
uvicorn[standard]>=0.30
beanie>=1.26
pydantic-settings>=2.4
PyJWT>=2.9
bcrypt>=4.2
Pillow>=10.4
python-multipart>=0.0.9
email-validator>=2.2
pytest>=8.3
pytest-asyncio>=0.24
httpx>=0.27
mongomock-motor>=0.0.31
```

- [ ] **Step 3: Create venv and install**

Run: `cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
Expected: installs without errors.

- [ ] **Step 4: Create `backend/pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

- [ ] **Step 5: Write the failing test `backend/tests/test_health.py`**

```python
async def test_health(api):
    resp = await api.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 6: Create minimal `backend/tests/conftest.py`** (extended in Task 2) **and an empty `backend/tests/__init__.py`** (later test files import helpers from sibling test modules with relative imports, which requires the package marker)

```python
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

- [ ] **Step 7: Create empty `backend/app/__init__.py`, then run test to verify it fails**

Run: `pytest tests/test_health.py -v`
Expected: FAIL (ModuleNotFoundError: app.main).

- [ ] **Step 8: Create `backend/app/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="Covareli API")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 9: Run test to verify it passes**

Run: `pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 10: Create `docker-compose.dev.yml`** (repo root; Mongo for local dev runs)

```yaml
services:
  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "Scaffold FastAPI backend with health endpoint and test harness"
```

---

### Task 2: Config, models, DB init

**Files:**
- Create: `backend/app/config.py`, `backend/app/timeutil.py`, `backend/app/db.py`, all files under `backend/app/models/`
- Modify: `backend/app/main.py`, `backend/tests/conftest.py`
- Test: `backend/tests/test_availability.py` (model smoke test only here)

- [ ] **Step 1: Create `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "covareli"
    jwt_secret: str = "dev-secret-change-me"
    jwt_expires_hours: int = 12
    cookie_secure: bool = False
    media_dir: str = "media"


config = AppConfig()
```

- [ ] **Step 2: Create `backend/app/timeutil.py`**

```python
from datetime import datetime, timezone


def to_naive_utc(dt: datetime) -> datetime:
    """Normalize any datetime to naive UTC (project-wide convention)."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

- [ ] **Step 3: Create `backend/app/models/common.py`**

```python
from enum import Enum

from pydantic import BaseModel


class LocalizedStr(BaseModel):
    ro: str = ""
    en: str = ""


class BodyType(str, Enum):
    hatchback = "hatchback"
    sedan = "sedan"
    suv = "suv"
    van = "van"
    wagon = "wagon"


class FuelType(str, Enum):
    petrol = "petrol"
    diesel = "diesel"
    hybrid = "hybrid"
    electric = "electric"


class Transmission(str, Enum):
    manual = "manual"
    automatic = "automatic"


class PriceTier(BaseModel):
    min_days: int
    max_days: int | None = None  # None = no upper bound
    price_per_day: int  # whole RON
```

- [ ] **Step 4: Create `backend/app/models/car.py`**

```python
from beanie import Document
from pydantic import Field

from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission


class Car(Document):
    brand: str
    model: str
    year: int
    body_type: BodyType
    fuel: FuelType
    transmission: Transmission
    seats: int
    doors: int
    engine: str = ""
    images: list[str] = Field(default_factory=list)  # filenames, ordered
    description: LocalizedStr = Field(default_factory=LocalizedStr)
    features: list[LocalizedStr] = Field(default_factory=list)
    price_tiers: list[PriceTier] = Field(default_factory=list)
    deposit_info: LocalizedStr = Field(default_factory=LocalizedStr)
    active: bool = True
    slug: str

    class Settings:
        name = "cars"
```

- [ ] **Step 5: Create `backend/app/models/location.py`**

```python
from beanie import Document
from pydantic import Field

from app.models.common import LocalizedStr


class Location(Document):
    name: LocalizedStr
    address: str = ""
    fee: int = 0  # whole RON
    active: bool = True
    sort_order: int = 0

    class Settings:
        name = "locations"
```

- [ ] **Step 6: Create `backend/app/models/booking.py`** (used by availability now; bookings API in Plan 2)

```python
from datetime import datetime
from enum import Enum

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

from app.timeutil import utcnow


class BookingStatus(str, Enum):
    pending_payment = "pending_payment"
    paid = "paid"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class Customer(BaseModel):
    name: str
    email: str
    phone: str


class PriceBreakdown(BaseModel):
    days: int
    price_per_day: int
    car_total: int
    pickup_fee: int = 0
    dropoff_fee: int = 0
    total: int


class Booking(Document):
    car_id: PydanticObjectId
    customer: Customer
    pickup_at: datetime
    dropoff_at: datetime
    pickup_location_id: PydanticObjectId
    dropoff_location_id: PydanticObjectId
    price: PriceBreakdown
    status: BookingStatus = BookingStatus.pending_payment
    netopia_ref: str = ""
    admin_notes: str = ""
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "bookings"
```

- [ ] **Step 7: Create `backend/app/models/contact_message.py`**

```python
from datetime import datetime

from beanie import Document
from pydantic import Field

from app.timeutil import utcnow


class ContactMessage(Document):
    name: str
    email: str
    phone: str = ""
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "contact_messages"
```

- [ ] **Step 8: Create `backend/app/models/settings_doc.py`** (singleton site settings)

```python
from enum import Enum

from beanie import Document


class PaymentMode(str, Enum):
    full = "full"
    advance_percent = "advance_percent"  # reserved, not used in v1 UI
    fixed_deposit = "fixed_deposit"      # reserved, not used in v1 UI


class SiteSettings(Document):
    payment_mode: PaymentMode = PaymentMode.full
    advance_value: int = 0  # percent or RON depending on mode
    contact_phone: str = "+40 749 323 172"
    contact_email: str = "office@covareli.ro"
    contact_address: str = "Str. Jupiter, nr. 1/12, Baciu, Cluj"

    class Settings:
        name = "settings"

    @classmethod
    async def get_singleton(cls) -> "SiteSettings":
        existing = await cls.find_one({})
        if existing:
            return existing
        created = cls()
        await created.insert()
        return created
```

- [ ] **Step 9: Create `backend/app/models/admin_user.py`**

```python
from beanie import Document


class AdminUser(Document):
    email: str
    password_hash: str

    class Settings:
        name = "admin_users"
```

- [ ] **Step 10: Create `backend/app/models/__init__.py`**

```python
from app.models.admin_user import AdminUser
from app.models.booking import Booking, BookingStatus, Customer, PriceBreakdown
from app.models.car import Car
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission
from app.models.contact_message import ContactMessage
from app.models.location import Location
from app.models.settings_doc import PaymentMode, SiteSettings

ALL_MODELS = [AdminUser, Booking, Car, ContactMessage, Location, SiteSettings]
```

- [ ] **Step 11: Create `backend/app/db.py`**

```python
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import config
from app.models import ALL_MODELS


async def init_db() -> None:
    client = AsyncIOMotorClient(config.mongo_url)
    await init_beanie(database=client[config.mongo_db], document_models=ALL_MODELS)
```

- [ ] **Step 12: Wire lifespan in `backend/app/main.py`** (replace the whole file)

```python
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
```

Note: httpx `ASGITransport` does not run lifespan, so tests are unaffected; tests init Beanie against mongomock in the fixture below.

- [ ] **Step 13: Extend `backend/tests/conftest.py`** (replace the whole file)

```python
import pytest_asyncio
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.models import ALL_MODELS


@pytest_asyncio.fixture
async def db():
    client = AsyncMongoMockClient()
    await init_beanie(database=client["test"], document_models=ALL_MODELS)


@pytest_asyncio.fixture
async def api(db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

- [ ] **Step 14: Write a model smoke test at the top of `backend/tests/test_availability.py`**

```python
from datetime import datetime

from beanie import PydanticObjectId

from app.models import Booking, BookingStatus, Customer, PriceBreakdown


def make_booking(car_id, pickup, dropoff, status, created_at=None):
    booking = Booking(
        car_id=car_id,
        customer=Customer(name="Test Client", email="client@test.ro", phone="0700000000"),
        pickup_at=pickup,
        dropoff_at=dropoff,
        pickup_location_id=PydanticObjectId(),
        dropoff_location_id=PydanticObjectId(),
        price=PriceBreakdown(days=1, price_per_day=200, car_total=200, total=200),
        status=status,
    )
    if created_at is not None:
        booking.created_at = created_at
    return booking


async def test_booking_roundtrip(db):
    car_id = PydanticObjectId()
    booking = make_booking(
        car_id, datetime(2026, 7, 1, 10), datetime(2026, 7, 3, 10), BookingStatus.paid
    )
    await booking.insert()
    found = await Booking.find_one(Booking.car_id == car_id)
    assert found is not None
    assert found.status == BookingStatus.paid
```

- [ ] **Step 15: Run tests**

Run: `pytest tests/ -v`
Expected: both tests PASS.

- [ ] **Step 16: Commit**

```bash
git add -A
git commit -m "Add config, Beanie models, and DB initialization"
```

---

### Task 3: Pricing logic (TDD)

**Files:**
- Create: `backend/app/pricing.py`
- Test: `backend/tests/test_pricing.py`

- [ ] **Step 1: Write failing tests `backend/tests/test_pricing.py`**

```python
from datetime import datetime

import pytest

from app.models.common import PriceTier
from app.pricing import price_per_day, quote_total, rental_days

TIERS = [
    PriceTier(min_days=1, max_days=2, price_per_day=250),
    PriceTier(min_days=3, max_days=6, price_per_day=220),
    PriceTier(min_days=7, max_days=None, price_per_day=190),
]


def test_rental_days_exact_24h_blocks():
    assert rental_days(datetime(2026, 7, 1, 10), datetime(2026, 7, 3, 10)) == 2


def test_rental_days_partial_day_rounds_up():
    assert rental_days(datetime(2026, 7, 1, 10), datetime(2026, 7, 3, 11)) == 3


def test_rental_days_minimum_one():
    assert rental_days(datetime(2026, 7, 1, 10), datetime(2026, 7, 1, 12)) == 1


def test_price_per_day_picks_matching_tier():
    assert price_per_day(TIERS, 1) == 250
    assert price_per_day(TIERS, 2) == 250
    assert price_per_day(TIERS, 3) == 220
    assert price_per_day(TIERS, 6) == 220
    assert price_per_day(TIERS, 7) == 190
    assert price_per_day(TIERS, 30) == 190


def test_price_per_day_no_match_raises():
    with pytest.raises(ValueError):
        price_per_day([PriceTier(min_days=2, max_days=None, price_per_day=100)], 1)


def test_quote_total_includes_location_fees():
    quote = quote_total(TIERS, datetime(2026, 7, 1, 10), datetime(2026, 7, 4, 10),
                        pickup_fee=50, dropoff_fee=0)
    assert quote.days == 3
    assert quote.price_per_day == 220
    assert quote.car_total == 660
    assert quote.pickup_fee == 50
    assert quote.total == 710
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pricing.py -v`
Expected: FAIL (ModuleNotFoundError: app.pricing).

- [ ] **Step 3: Implement `backend/app/pricing.py`**

```python
import math
from datetime import datetime

from app.models.booking import PriceBreakdown
from app.models.common import PriceTier
from app.timeutil import to_naive_utc


def rental_days(pickup: datetime, dropoff: datetime) -> int:
    seconds = (to_naive_utc(dropoff) - to_naive_utc(pickup)).total_seconds()
    return max(1, math.ceil(seconds / 86400))


def price_per_day(tiers: list[PriceTier], days: int) -> int:
    for tier in tiers:
        if days >= tier.min_days and (tier.max_days is None or days <= tier.max_days):
            return tier.price_per_day
    raise ValueError(f"no price tier matches a rental of {days} days")


def quote_total(tiers: list[PriceTier], pickup: datetime, dropoff: datetime,
                pickup_fee: int = 0, dropoff_fee: int = 0) -> PriceBreakdown:
    days = rental_days(pickup, dropoff)
    ppd = price_per_day(tiers, days)
    car_total = days * ppd
    return PriceBreakdown(
        days=days,
        price_per_day=ppd,
        car_total=car_total,
        pickup_fee=pickup_fee,
        dropoff_fee=dropoff_fee,
        total=car_total + pickup_fee + dropoff_fee,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_pricing.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Add rental pricing logic with duration tiers"
```

---

### Task 4: Availability logic (TDD)

**Files:**
- Create: `backend/app/availability.py`
- Test: `backend/tests/test_availability.py` (append to file from Task 2)

Availability rule (from spec): a car is available for [start, end) if no overlapping booking exists with status `paid`/`confirmed`, and no overlapping `pending_payment` booking created in the last 30 minutes. Overlap: `pickup_at < end AND dropoff_at > start`.

- [ ] **Step 1: Append failing tests to `backend/tests/test_availability.py`**

```python
from datetime import timedelta

from app.availability import booked_ranges, car_is_available
from app.timeutil import utcnow


async def test_no_bookings_means_available(db):
    assert await car_is_available(
        PydanticObjectId(), datetime(2026, 7, 1, 10), datetime(2026, 7, 5, 10)
    )


async def test_overlapping_paid_booking_blocks(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.paid
    ).insert()
    assert not await car_is_available(
        car_id, datetime(2026, 7, 3, 10), datetime(2026, 7, 6, 10)
    )


async def test_adjacent_booking_does_not_block(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 1, 10), datetime(2026, 7, 3, 10), BookingStatus.confirmed
    ).insert()
    # starts exactly when the other ends
    assert await car_is_available(
        car_id, datetime(2026, 7, 3, 10), datetime(2026, 7, 5, 10)
    )


async def test_cancelled_booking_does_not_block(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.cancelled
    ).insert()
    assert await car_is_available(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10)
    )


async def test_fresh_pending_payment_blocks(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10),
        BookingStatus.pending_payment, created_at=utcnow(),
    ).insert()
    assert not await car_is_available(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10)
    )


async def test_expired_pending_payment_does_not_block(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10),
        BookingStatus.pending_payment, created_at=utcnow() - timedelta(minutes=31),
    ).insert()
    assert await car_is_available(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10)
    )


async def test_booked_ranges_returns_blocking_intervals_only(db):
    car_id = PydanticObjectId()
    await make_booking(
        car_id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.paid
    ).insert()
    await make_booking(
        car_id, datetime(2026, 7, 10, 10), datetime(2026, 7, 12, 10), BookingStatus.cancelled
    ).insert()
    ranges = await booked_ranges(car_id)
    assert ranges == [(datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10))]
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `pytest tests/test_availability.py -v`
Expected: roundtrip test PASS, the rest FAIL (ModuleNotFoundError: app.availability).

- [ ] **Step 3: Implement `backend/app/availability.py`**

```python
from datetime import datetime, timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.logical import And, Or
from beanie.odm.operators.find.comparison import In

from app.models.booking import Booking, BookingStatus
from app.timeutil import to_naive_utc, utcnow

PENDING_HOLD_MINUTES = 30


def _blocking_filter():
    hold_cutoff = utcnow() - timedelta(minutes=PENDING_HOLD_MINUTES)
    return Or(
        In(Booking.status, [BookingStatus.paid, BookingStatus.confirmed]),
        And(
            Booking.status == BookingStatus.pending_payment,
            Booking.created_at > hold_cutoff,
        ),
    )


async def car_is_available(
    car_id: PydanticObjectId, start: datetime, end: datetime
) -> bool:
    start, end = to_naive_utc(start), to_naive_utc(end)
    count = await Booking.find(
        Booking.car_id == car_id,
        Booking.pickup_at < end,
        Booking.dropoff_at > start,
        _blocking_filter(),
    ).count()
    return count == 0


async def booked_ranges(
    car_id: PydanticObjectId,
) -> list[tuple[datetime, datetime]]:
    bookings = await Booking.find(
        Booking.car_id == car_id, _blocking_filter()
    ).sort("+pickup_at").to_list()
    return [(b.pickup_at, b.dropoff_at) for b in bookings]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_availability.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Add car availability logic with pending-payment hold window"
```

---

### Task 5: Admin auth (security utils, login routes, guard dependency, seed script)

**Files:**
- Create: `backend/app/auth/__init__.py` (empty), `backend/app/auth/security.py`, `backend/app/auth/deps.py`, `backend/app/auth/routes.py`, `backend/scripts/seed_admin.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing tests `backend/tests/test_auth.py`**

```python
from app.auth.security import create_token, decode_token, hash_password, verify_password
from app.models import AdminUser


def test_password_hash_roundtrip():
    h = hash_password("secret123")
    assert h != "secret123"
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    token = create_token("admin@test.ro")
    assert decode_token(token) == "admin@test.ro"
    assert decode_token("garbage") is None


async def make_admin(email="admin@test.ro", password="secret123"):
    await AdminUser(email=email, password_hash=hash_password(password)).insert()


async def test_login_sets_cookie_and_me_works(api):
    await make_admin()
    resp = await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    assert resp.status_code == 200
    assert "admin_token" in resp.cookies
    me = await api.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "admin@test.ro"


async def test_login_wrong_password_rejected(api):
    await make_admin()
    resp = await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "nope"}
    )
    assert resp.status_code == 401


async def test_me_without_cookie_rejected(api):
    resp = await api.get("/api/auth/me")
    assert resp.status_code == 401


async def test_logout_clears_cookie(api):
    await make_admin()
    await api.post("/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"})
    await api.post("/api/auth/logout")
    resp = await api.get("/api/auth/me")
    assert resp.status_code == 401


async def test_change_password(api):
    await make_admin()
    await api.post("/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"})
    resp = await api.post(
        "/api/auth/change-password",
        json={"current_password": "secret123", "new_password": "newsecret456"},
    )
    assert resp.status_code == 200
    resp = await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "newsecret456"}
    )
    assert resp.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_auth.py -v`
Expected: FAIL (ModuleNotFoundError: app.auth.security).

- [ ] **Step 3: Implement `backend/app/auth/security.py`**

```python
from datetime import timedelta

import bcrypt
import jwt

from app.config import config
from app.timeutil import utcnow


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": utcnow() + timedelta(hours=config.jwt_expires_hours),
    }
    return jwt.encode(payload, config.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=["HS256"])
        return payload["sub"]
    except jwt.InvalidTokenError:
        return None
```

- [ ] **Step 4: Implement `backend/app/auth/deps.py`**

```python
from fastapi import Cookie, HTTPException

from app.auth.security import decode_token
from app.models import AdminUser

COOKIE_NAME = "admin_token"


async def require_admin(admin_token: str | None = Cookie(default=None)) -> AdminUser:
    email = decode_token(admin_token) if admin_token else None
    if email is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await AdminUser.find_one(AdminUser.email == email)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
```

- [ ] **Step 5: Implement `backend/app/auth/routes.py`** (with a small in-memory login throttle)

```python
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app.auth.deps import COOKIE_NAME, require_admin
from app.auth.security import create_token, hash_password, verify_password
from app.config import config
from app.models import AdminUser

router = APIRouter(prefix="/api/auth", tags=["auth"])

MAX_ATTEMPTS = 10
WINDOW_SECONDS = 300
_attempts: dict[str, list[float]] = defaultdict(list)


def _throttle(ip: str) -> None:
    now = time.monotonic()
    _attempts[ip] = [t for t in _attempts[ip] if now - t < WINDOW_SECONDS]
    if len(_attempts[ip]) >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts")
    _attempts[ip].append(now)


class LoginBody(BaseModel):
    email: str
    password: str


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
async def login(body: LoginBody, request: Request, response: Response):
    _throttle(request.client.host if request.client else "unknown")
    user = await AdminUser.find_one(AdminUser.email == body.email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    response.set_cookie(
        COOKIE_NAME,
        create_token(user.email),
        httponly=True,
        secure=config.cookie_secure,
        samesite="lax",
        max_age=config.jwt_expires_hours * 3600,
    )
    return {"email": user.email}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
async def me(user: AdminUser = Depends(require_admin)):
    return {"email": user.email}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordBody, user: AdminUser = Depends(require_admin)
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is wrong")
    if len(body.new_password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters")
    user.password_hash = hash_password(body.new_password)
    await user.save()
    return {"ok": True}
```

- [ ] **Step 6: Mount the router in `backend/app/main.py`** (add below `app = FastAPI(...)`)

```python
from app.auth.routes import router as auth_router

app.include_router(auth_router)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/test_auth.py -v`
Expected: all PASS.

- [ ] **Step 8: Create `backend/scripts/seed_admin.py`**

```python
"""Create or update the admin user. Usage:
    python scripts/seed_admin.py admin@covareli.ro 'strong-password-here'
"""
import asyncio
import sys

sys.path.insert(0, ".")

from app.auth.security import hash_password  # noqa: E402
from app.db import init_db  # noqa: E402
from app.models import AdminUser  # noqa: E402


async def main(email: str, password: str) -> None:
    await init_db()
    existing = await AdminUser.find_one(AdminUser.email == email)
    if existing:
        existing.password_hash = hash_password(password)
        await existing.save()
        print(f"Updated password for {email}")
    else:
        await AdminUser(email=email, password_hash=hash_password(password)).insert()
        print(f"Created admin {email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
```

- [ ] **Step 9: Run the full suite**

Run: `pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "Add admin auth with JWT cookie, login throttle, and seed script"
```

---

### Task 6: Locations CRUD (admin) + public list

**Files:**
- Create: `backend/app/routers/__init__.py` (empty), `backend/app/routers/admin_locations.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_locations.py`

Public listing of locations is part of `public.py` in Task 9; this task covers the admin CRUD.

- [ ] **Step 1: Write failing tests `backend/tests/test_locations.py`**

```python
import pytest_asyncio

from app.auth.security import hash_password
from app.models import AdminUser

LOCATION = {
    "name": {"ro": "Sediu Baciu", "en": "Baciu Office"},
    "address": "Str. Jupiter 1/12, Baciu",
    "fee": 0,
    "active": True,
    "sort_order": 1,
}


@pytest_asyncio.fixture
async def admin(api):
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    resp = await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    assert resp.status_code == 200
    return api


async def test_crud_requires_auth(api):
    resp = await api.post("/api/admin/locations", json=LOCATION)
    assert resp.status_code == 401


async def test_location_crud_cycle(admin):
    resp = await admin.post("/api/admin/locations", json=LOCATION)
    assert resp.status_code == 201
    loc_id = resp.json()["id"]

    resp = await admin.get("/api/admin/locations")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await admin.put(f"/api/admin/locations/{loc_id}", json={**LOCATION, "fee": 50})
    assert resp.status_code == 200
    assert resp.json()["fee"] == 50

    resp = await admin.delete(f"/api/admin/locations/{loc_id}")
    assert resp.status_code == 204

    resp = await admin.get("/api/admin/locations")
    assert resp.json() == []


async def test_update_missing_location_404(admin):
    resp = await admin.put("/api/admin/locations/64b000000000000000000000", json=LOCATION)
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_locations.py -v`
Expected: FAIL (404s instead of expected codes — routes don't exist).

- [ ] **Step 3: Implement `backend/app/routers/admin_locations.py`**

```python
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.auth.deps import require_admin
from app.models import Location
from app.models.common import LocalizedStr

router = APIRouter(
    prefix="/api/admin/locations",
    tags=["admin:locations"],
    dependencies=[Depends(require_admin)],
)


class LocationBody(BaseModel):
    name: LocalizedStr
    address: str = ""
    fee: int = Field(default=0, ge=0)
    active: bool = True
    sort_order: int = 0


def serialize(loc: Location) -> dict:
    return {
        "id": str(loc.id),
        "name": loc.name.model_dump(),
        "address": loc.address,
        "fee": loc.fee,
        "active": loc.active,
        "sort_order": loc.sort_order,
    }


async def get_or_404(location_id: PydanticObjectId) -> Location:
    loc = await Location.get(location_id)
    if loc is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc


@router.get("")
async def list_locations():
    locs = await Location.find_all().sort("+sort_order").to_list()
    return [serialize(l) for l in locs]


@router.post("", status_code=201)
async def create_location(body: LocationBody):
    loc = Location(**body.model_dump())
    await loc.insert()
    return serialize(loc)


@router.put("/{location_id}")
async def update_location(location_id: PydanticObjectId, body: LocationBody):
    loc = await get_or_404(location_id)
    for key, value in body.model_dump().items():
        setattr(loc, key, value)
    await loc.save()
    return serialize(loc)


@router.delete("/{location_id}", status_code=204)
async def delete_location(location_id: PydanticObjectId):
    loc = await get_or_404(location_id)
    await loc.delete()
    return Response(status_code=204)
```

Note on `LocationBody(**body.model_dump())`: Location's `name` field accepts the dumped dict because Beanie re-validates on assignment of the full model; constructing `Location(**body.model_dump())` re-parses nested dicts into `LocalizedStr`.

- [ ] **Step 4: Mount router in `backend/app/main.py`**

```python
from app.routers.admin_locations import router as admin_locations_router

app.include_router(admin_locations_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_locations.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Add admin locations CRUD"
```

---

### Task 7: Slug helper + Cars CRUD (admin)

**Files:**
- Create: `backend/app/slugs.py`, `backend/app/routers/admin_cars.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_cars_admin.py`

- [ ] **Step 1: Write failing tests `backend/tests/test_cars_admin.py`**

```python
import pytest_asyncio

from app.auth.security import hash_password
from app.models import AdminUser, Car
from app.slugs import slugify

CAR = {
    "brand": "Audi",
    "model": "A6 AllRoad",
    "year": 2022,
    "body_type": "wagon",
    "fuel": "diesel",
    "transmission": "automatic",
    "seats": 5,
    "doors": 5,
    "engine": "3.0 TDI",
    "description": {"ro": "Break premium", "en": "Premium wagon"},
    "features": [{"ro": "Navigație", "en": "Navigation"}],
    "price_tiers": [
        {"min_days": 1, "max_days": 2, "price_per_day": 350},
        {"min_days": 3, "max_days": None, "price_per_day": 300},
    ],
    "deposit_info": {"ro": "Garanție 1000 lei", "en": "1000 RON deposit"},
    "active": True,
}


def test_slugify():
    assert slugify("Audi A6 AllRoad 2022") == "audi-a6-allroad-2022"
    assert slugify("Škoda Octavia") == "skoda-octavia"


@pytest_asyncio.fixture
async def admin(api):
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    return api


async def test_create_car_generates_unique_slug(admin):
    resp = await admin.post("/api/admin/cars", json=CAR)
    assert resp.status_code == 201
    assert resp.json()["slug"] == "audi-a6-allroad-2022"

    resp = await admin.post("/api/admin/cars", json=CAR)
    assert resp.status_code == 201
    assert resp.json()["slug"] == "audi-a6-allroad-2022-2"


async def test_car_crud_cycle(admin):
    created = (await admin.post("/api/admin/cars", json=CAR)).json()
    car_id = created["id"]

    resp = await admin.get("/api/admin/cars")
    assert len(resp.json()) == 1

    resp = await admin.put(f"/api/admin/cars/{car_id}", json={**CAR, "seats": 4})
    assert resp.status_code == 200
    assert resp.json()["seats"] == 4
    # slug unchanged on update
    assert resp.json()["slug"] == "audi-a6-allroad-2022"

    resp = await admin.delete(f"/api/admin/cars/{car_id}")
    assert resp.status_code == 204
    assert await Car.find_all().count() == 0


async def test_invalid_price_tiers_rejected(admin):
    bad = {**CAR, "price_tiers": []}
    resp = await admin.post("/api/admin/cars", json=bad)
    assert resp.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cars_admin.py -v`
Expected: FAIL (ModuleNotFoundError: app.slugs).

- [ ] **Step 3: Implement `backend/app/slugs.py`**

```python
import re
import unicodedata


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return text.strip("-")


async def unique_car_slug(base_text: str) -> str:
    from app.models import Car

    base = slugify(base_text)
    slug = base
    counter = 2
    while await Car.find_one(Car.slug == slug) is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug
```

- [ ] **Step 4: Implement `backend/app/routers/admin_cars.py`**

```python
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.auth.deps import require_admin
from app.models import Car
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission
from app.slugs import unique_car_slug

router = APIRouter(
    prefix="/api/admin/cars",
    tags=["admin:cars"],
    dependencies=[Depends(require_admin)],
)


class CarBody(BaseModel):
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    year: int = Field(ge=1990, le=2100)
    body_type: BodyType
    fuel: FuelType
    transmission: Transmission
    seats: int = Field(ge=1, le=9)
    doors: int = Field(ge=2, le=6)
    engine: str = ""
    description: LocalizedStr = Field(default_factory=LocalizedStr)
    features: list[LocalizedStr] = Field(default_factory=list)
    price_tiers: list[PriceTier] = Field(min_length=1)
    deposit_info: LocalizedStr = Field(default_factory=LocalizedStr)
    active: bool = True


def serialize(car: Car) -> dict:
    data = car.model_dump(exclude={"id", "revision_id"})
    data["id"] = str(car.id)
    return data


async def get_or_404(car_id: PydanticObjectId) -> Car:
    car = await Car.get(car_id)
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.get("")
async def list_cars():
    cars = await Car.find_all().sort("+brand", "+model").to_list()
    return [serialize(c) for c in cars]


@router.post("", status_code=201)
async def create_car(body: CarBody):
    slug = await unique_car_slug(f"{body.brand} {body.model} {body.year}")
    car = Car(**body.model_dump(), slug=slug)
    await car.insert()
    return serialize(car)


@router.put("/{car_id}")
async def update_car(car_id: PydanticObjectId, body: CarBody):
    car = await get_or_404(car_id)
    for key, value in body.model_dump().items():
        setattr(car, key, value)
    await car.save()
    return serialize(car)


@router.delete("/{car_id}", status_code=204)
async def delete_car(car_id: PydanticObjectId):
    car = await get_or_404(car_id)
    await car.delete()
    return Response(status_code=204)
```

- [ ] **Step 5: Mount router in `backend/app/main.py`**

```python
from app.routers.admin_cars import router as admin_cars_router

app.include_router(admin_cars_router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_cars_admin.py -v`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "Add slug helper and admin cars CRUD"
```

---

### Task 8: Car image upload, resize, delete, reorder

**Files:**
- Create: `backend/app/images.py`
- Modify: `backend/app/routers/admin_cars.py`, `backend/app/main.py`
- Test: `backend/tests/test_images.py`

Design: POST a multipart image to `/api/admin/cars/{id}/images`. The file is validated (JPEG/PNG/WebP, ≤ 10 MB), resized into two WebP variants — `card` (640px wide) and `full` (1600px wide) — saved under `{media_dir}/cars/{car_id}/{uuid}_card.webp` / `_full.webp`. The base name `{uuid}` is appended to `car.images`. The frontend builds URLs as `/media/cars/{car_id}/{name}_card.webp`.

- [ ] **Step 1: Write failing tests `backend/tests/test_images.py`**

```python
import io

import pytest_asyncio
from PIL import Image

from app.auth.security import hash_password
from app.config import config
from app.models import AdminUser

from .test_cars_admin import CAR


@pytest_asyncio.fixture
async def admin(api, tmp_path):
    config.media_dir = str(tmp_path)
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    return api


def png_bytes(width=2000, height=1200) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(120, 30, 30)).save(buf, format="PNG")
    return buf.getvalue()


async def create_car(admin) -> str:
    resp = await admin.post("/api/admin/cars", json=CAR)
    return resp.json()["id"]


async def test_upload_creates_variants_and_updates_car(admin, tmp_path):
    car_id = await create_car(admin)
    resp = await admin.post(
        f"/api/admin/cars/{car_id}/images",
        files={"file": ("photo.png", png_bytes(), "image/png")},
    )
    assert resp.status_code == 201
    name = resp.json()["name"]
    card = tmp_path / "cars" / car_id / f"{name}_card.webp"
    full = tmp_path / "cars" / car_id / f"{name}_full.webp"
    assert card.exists() and full.exists()
    assert Image.open(card).width == 640
    assert Image.open(full).width == 1600

    car = (await admin.get("/api/admin/cars")).json()[0]
    assert car["images"] == [name]


async def test_upload_rejects_non_image(admin):
    car_id = await create_car(admin)
    resp = await admin.post(
        f"/api/admin/cars/{car_id}/images",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 415


async def test_reorder_and_delete_image(admin, tmp_path):
    car_id = await create_car(admin)
    names = []
    for _ in range(2):
        resp = await admin.post(
            f"/api/admin/cars/{car_id}/images",
            files={"file": ("p.png", png_bytes(), "image/png")},
        )
        names.append(resp.json()["name"])

    resp = await admin.put(
        f"/api/admin/cars/{car_id}/images/order", json={"images": names[::-1]}
    )
    assert resp.status_code == 200
    assert resp.json()["images"] == names[::-1]

    resp = await admin.delete(f"/api/admin/cars/{car_id}/images/{names[0]}")
    assert resp.status_code == 200
    assert resp.json()["images"] == [names[1]]
    assert not (tmp_path / "cars" / car_id / f"{names[0]}_card.webp").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_images.py -v`
Expected: FAIL (405/404 — endpoints don't exist).

- [ ] **Step 3: Implement `backend/app/images.py`**

```python
import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

from app.config import config

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024
VARIANTS = {"card": 640, "full": 1600}


def car_media_dir(car_id: str) -> Path:
    return Path(config.media_dir) / "cars" / car_id


async def save_car_image(car_id: str, file: UploadFile) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG or WebP images allowed")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image larger than 10 MB")
    try:
        original = Image.open(io.BytesIO(raw))
        original.load()
    except Exception:
        raise HTTPException(status_code=415, detail="File is not a valid image")

    name = uuid.uuid4().hex
    target_dir = car_media_dir(car_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    for variant, width in VARIANTS.items():
        img = original.convert("RGB")
        if img.width > width:
            height = round(img.height * width / img.width)
            img = img.resize((width, height), Image.LANCZOS)
        img.save(target_dir / f"{name}_{variant}.webp", format="WEBP", quality=80)
    return name


def delete_car_image(car_id: str, name: str) -> None:
    for variant in VARIANTS:
        path = car_media_dir(car_id) / f"{name}_{variant}.webp"
        path.unlink(missing_ok=True)
```

Note: the test resizes a 2000px image down; `Image.open(card).width == 640` holds because source is wider than both variants. The `img.resize` call above produces exactly the requested width.

- [ ] **Step 4: Add image endpoints to `backend/app/routers/admin_cars.py`** (append)

```python
from fastapi import UploadFile

from app.images import delete_car_image, save_car_image


class ImageOrderBody(BaseModel):
    images: list[str]


@router.post("/{car_id}/images", status_code=201)
async def upload_image(car_id: PydanticObjectId, file: UploadFile):
    car = await get_or_404(car_id)
    name = await save_car_image(str(car.id), file)
    car.images.append(name)
    await car.save()
    return {"name": name, "images": car.images}


@router.put("/{car_id}/images/order")
async def reorder_images(car_id: PydanticObjectId, body: ImageOrderBody):
    car = await get_or_404(car_id)
    if sorted(body.images) != sorted(car.images):
        raise HTTPException(status_code=400, detail="Image list does not match car images")
    car.images = body.images
    await car.save()
    return {"images": car.images}


@router.delete("/{car_id}/images/{name}")
async def delete_image(car_id: PydanticObjectId, name: str):
    car = await get_or_404(car_id)
    if name not in car.images:
        raise HTTPException(status_code=404, detail="Image not found")
    delete_car_image(str(car.id), name)
    car.images.remove(name)
    await car.save()
    return {"images": car.images}
```

- [ ] **Step 5: Serve media statically — modify `backend/app/main.py`** (after `app = FastAPI(...)`)

```python
from pathlib import Path

from fastapi.staticfiles import StaticFiles

from app.config import config

Path(config.media_dir).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=config.media_dir), name="media")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_images.py -v`
Expected: all PASS.

- [ ] **Step 7: Run full suite and commit**

Run: `pytest tests/ -v` — Expected: all PASS.

```bash
git add -A
git commit -m "Add car image upload with WebP variants, reorder and delete"
```

---

### Task 9: Public API (cars with filters + availability, car detail, booked ranges, locations)

**Files:**
- Create: `backend/app/routers/public.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_public.py`

Endpoints:
- `GET /api/cars?body_type=&fuel=&transmission=&seats_min=&from=&to=` — active cars only; when `from`+`to` (ISO datetimes) are given, exclude unavailable cars. Response includes `price_from` (lowest tier price) for "from X lei/day" cards.
- `GET /api/cars/{slug}` — full car detail (active only).
- `GET /api/cars/{slug}/booked-ranges` — blocking intervals for the date picker.
- `GET /api/locations` — active locations sorted by `sort_order`, with fees.

- [ ] **Step 1: Write failing tests `backend/tests/test_public.py`**

```python
from datetime import datetime

from app.models import Car, Location
from app.models.common import LocalizedStr, PriceTier

from .test_availability import make_booking
from app.models import BookingStatus


def make_car(brand="Dacia", model="Logan", slug="dacia-logan-2023", active=True,
             fuel="petrol", body_type="sedan") -> Car:
    return Car(
        brand=brand, model=model, year=2023, body_type=body_type, fuel=fuel,
        transmission="manual", seats=5, doors=4,
        price_tiers=[
            PriceTier(min_days=1, max_days=2, price_per_day=200),
            PriceTier(min_days=3, max_days=None, price_per_day=180),
        ],
        active=active, slug=slug,
    )


async def test_list_only_active_cars(api):
    await make_car().insert()
    await make_car(slug="hidden-car", active=False).insert()
    resp = await api.get("/api/cars")
    assert resp.status_code == 200
    cars = resp.json()
    assert len(cars) == 1
    assert cars[0]["slug"] == "dacia-logan-2023"
    assert cars[0]["price_from"] == 180


async def test_list_filters_by_fuel(api):
    await make_car().insert()
    await make_car(slug="tesla", fuel="electric").insert()
    resp = await api.get("/api/cars", params={"fuel": "electric"})
    assert [c["slug"] for c in resp.json()] == ["tesla"]


async def test_list_with_dates_excludes_booked_car(api):
    car = make_car()
    await car.insert()
    await make_booking(
        car.id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.paid
    ).insert()
    resp = await api.get("/api/cars", params={
        "from": "2026-07-03T10:00:00", "to": "2026-07-05T10:00:00"
    })
    assert resp.json() == []
    resp = await api.get("/api/cars", params={
        "from": "2026-07-10T10:00:00", "to": "2026-07-12T10:00:00"
    })
    assert len(resp.json()) == 1


async def test_car_detail_by_slug(api):
    await make_car().insert()
    resp = await api.get("/api/cars/dacia-logan-2023")
    assert resp.status_code == 200
    assert resp.json()["brand"] == "Dacia"
    resp = await api.get("/api/cars/missing")
    assert resp.status_code == 404


async def test_inactive_car_detail_404(api):
    await make_car(active=False).insert()
    resp = await api.get("/api/cars/dacia-logan-2023")
    assert resp.status_code == 404


async def test_booked_ranges_endpoint(api):
    car = make_car()
    await car.insert()
    await make_booking(
        car.id, datetime(2026, 7, 2, 10), datetime(2026, 7, 4, 10), BookingStatus.paid
    ).insert()
    resp = await api.get("/api/cars/dacia-logan-2023/booked-ranges")
    assert resp.status_code == 200
    assert resp.json() == [
        {"start": "2026-07-02T10:00:00", "end": "2026-07-04T10:00:00"}
    ]


async def test_public_locations_active_sorted(api):
    await Location(name=LocalizedStr(ro="Aeroport", en="Airport"), fee=50, sort_order=2).insert()
    await Location(name=LocalizedStr(ro="Sediu", en="Office"), fee=0, sort_order=1).insert()
    await Location(name=LocalizedStr(ro="Ascuns", en="Hidden"), active=False).insert()
    resp = await api.get("/api/locations")
    names = [l["name"]["ro"] for l in resp.json()]
    assert names == ["Sediu", "Aeroport"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_public.py -v`
Expected: FAIL (404s — routes don't exist).

- [ ] **Step 3: Implement `backend/app/routers/public.py`**

```python
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.availability import booked_ranges as get_booked_ranges
from app.availability import car_is_available
from app.models import Car, Location
from app.models.common import BodyType, FuelType, Transmission

router = APIRouter(prefix="/api", tags=["public"])


def serialize_car(car: Car) -> dict:
    data = car.model_dump(exclude={"id", "revision_id"})
    data["id"] = str(car.id)
    data["price_from"] = min(t.price_per_day for t in car.price_tiers)
    return data


@router.get("/cars")
async def list_cars(
    body_type: BodyType | None = None,
    fuel: FuelType | None = None,
    transmission: Transmission | None = None,
    seats_min: int | None = None,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
):
    query = Car.find(Car.active == True)  # noqa: E712
    if body_type is not None:
        query = query.find(Car.body_type == body_type)
    if fuel is not None:
        query = query.find(Car.fuel == fuel)
    if transmission is not None:
        query = query.find(Car.transmission == transmission)
    if seats_min is not None:
        query = query.find(Car.seats >= seats_min)
    cars = await query.sort("+brand", "+model").to_list()

    if from_ is not None and to is not None:
        if to <= from_:
            raise HTTPException(status_code=422, detail="'to' must be after 'from'")
        available = []
        for car in cars:
            if await car_is_available(car.id, from_, to):
                available.append(car)
        cars = available

    return [serialize_car(c) for c in cars]


async def active_car_by_slug(slug: str) -> Car:
    car = await Car.find_one(Car.slug == slug, Car.active == True)  # noqa: E712
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.get("/cars/{slug}")
async def car_detail(slug: str):
    return serialize_car(await active_car_by_slug(slug))


@router.get("/cars/{slug}/booked-ranges")
async def car_booked_ranges(slug: str):
    car = await active_car_by_slug(slug)
    ranges = await get_booked_ranges(car.id)
    return [
        {"start": start.isoformat(), "end": end.isoformat()}
        for start, end in ranges
    ]


@router.get("/locations")
async def list_locations():
    locs = await Location.find(Location.active == True).sort("+sort_order").to_list()  # noqa: E712
    return [
        {"id": str(l.id), "name": l.name.model_dump(), "address": l.address, "fee": l.fee}
        for l in locs
    ]
```

- [ ] **Step 4: Mount router in `backend/app/main.py`**

```python
from app.routers.public import router as public_router

app.include_router(public_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_public.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Add public API: car listing with filters and availability, detail, locations"
```

---

### Task 10: Contact form, admin messages inbox, settings endpoints

**Files:**
- Create: `backend/app/routers/admin_messages.py`, `backend/app/routers/admin_settings.py`
- Modify: `backend/app/routers/public.py`, `backend/app/main.py`
- Test: `backend/tests/test_contact_and_settings.py`

(Contact email notification to admin ships in Plan 2 together with the SMTP module; here the message is stored only.)

- [ ] **Step 1: Write failing tests `backend/tests/test_contact_and_settings.py`**

```python
import pytest_asyncio

from app.auth.security import hash_password
from app.models import AdminUser, ContactMessage


@pytest_asyncio.fixture
async def admin(api):
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    await api.post(
        "/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"}
    )
    return api


async def test_contact_form_saves_message(api):
    resp = await api.post("/api/contact", json={
        "name": "Ion Pop", "email": "ion@example.com",
        "phone": "0744111222", "message": "Aveți mașini libere în iulie?",
    })
    assert resp.status_code == 201
    assert await ContactMessage.find_all().count() == 1


async def test_contact_form_validates(api):
    resp = await api.post("/api/contact", json={"name": "", "email": "x", "message": ""})
    assert resp.status_code == 422


async def test_admin_lists_and_marks_messages(admin):
    await admin.post("/api/contact", json={
        "name": "Ion Pop", "email": "ion@example.com", "message": "Salut",
    })
    resp = await admin.get("/api/admin/messages")
    assert resp.status_code == 200
    msg = resp.json()[0]
    assert msg["read"] is False

    resp = await admin.put(f"/api/admin/messages/{msg['id']}/read", json={"read": True})
    assert resp.status_code == 200
    assert resp.json()["read"] is True


async def test_messages_require_auth(api):
    resp = await api.get("/api/admin/messages")
    assert resp.status_code == 401


async def test_settings_roundtrip(admin):
    resp = await admin.get("/api/admin/settings")
    assert resp.status_code == 200
    assert resp.json()["payment_mode"] == "full"

    resp = await admin.put("/api/admin/settings", json={
        "payment_mode": "full", "advance_value": 0,
        "contact_phone": "+40 700 000 000",
        "contact_email": "office@covareli.ro",
        "contact_address": "Adresa nouă",
    })
    assert resp.status_code == 200
    assert resp.json()["contact_phone"] == "+40 700 000 000"


async def test_public_site_info(api):
    resp = await api.get("/api/site-info")
    assert resp.status_code == 200
    body = resp.json()
    assert "contact_phone" in body and "payment_mode" in body
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_contact_and_settings.py -v`
Expected: FAIL (404s).

- [ ] **Step 3: Add contact + site-info to `backend/app/routers/public.py`** (append)

```python
from pydantic import BaseModel, EmailStr, Field

from app.models import ContactMessage, SiteSettings


class ContactBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str = Field(default="", max_length=30)
    message: str = Field(min_length=1, max_length=5000)


@router.post("/contact", status_code=201)
async def submit_contact(body: ContactBody):
    msg = ContactMessage(**body.model_dump())
    await msg.insert()
    return {"ok": True}


@router.get("/site-info")
async def site_info():
    s = await SiteSettings.get_singleton()
    return {
        "payment_mode": s.payment_mode,
        "advance_value": s.advance_value,
        "contact_phone": s.contact_phone,
        "contact_email": s.contact_email,
        "contact_address": s.contact_address,
    }
```

- [ ] **Step 4: Implement `backend/app/routers/admin_messages.py`**

```python
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.deps import require_admin
from app.models import ContactMessage

router = APIRouter(
    prefix="/api/admin/messages",
    tags=["admin:messages"],
    dependencies=[Depends(require_admin)],
)


def serialize(msg: ContactMessage) -> dict:
    return {
        "id": str(msg.id),
        "name": msg.name,
        "email": msg.email,
        "phone": msg.phone,
        "message": msg.message,
        "read": msg.read,
        "created_at": msg.created_at.isoformat(),
    }


class ReadBody(BaseModel):
    read: bool


@router.get("")
async def list_messages():
    msgs = await ContactMessage.find_all().sort("-created_at").to_list()
    return [serialize(m) for m in msgs]


@router.put("/{message_id}/read")
async def mark_read(message_id: PydanticObjectId, body: ReadBody):
    msg = await ContactMessage.get(message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.read = body.read
    await msg.save()
    return serialize(msg)
```

- [ ] **Step 5: Implement `backend/app/routers/admin_settings.py`**

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.deps import require_admin
from app.models import SiteSettings
from app.models.settings_doc import PaymentMode

router = APIRouter(
    prefix="/api/admin/settings",
    tags=["admin:settings"],
    dependencies=[Depends(require_admin)],
)


class SettingsBody(BaseModel):
    payment_mode: PaymentMode
    advance_value: int = Field(ge=0)
    contact_phone: str
    contact_email: str
    contact_address: str


def serialize(s: SiteSettings) -> dict:
    return {
        "payment_mode": s.payment_mode,
        "advance_value": s.advance_value,
        "contact_phone": s.contact_phone,
        "contact_email": s.contact_email,
        "contact_address": s.contact_address,
    }


@router.get("")
async def get_settings():
    return serialize(await SiteSettings.get_singleton())


@router.put("")
async def update_settings(body: SettingsBody):
    s = await SiteSettings.get_singleton()
    for key, value in body.model_dump().items():
        setattr(s, key, value)
    await s.save()
    return serialize(s)
```

- [ ] **Step 6: Mount the two routers in `backend/app/main.py`**

```python
from app.routers.admin_messages import router as admin_messages_router
from app.routers.admin_settings import router as admin_settings_router

app.include_router(admin_messages_router)
app.include_router(admin_settings_router)
```

- [ ] **Step 7: Run tests to verify they pass, then full suite**

Run: `pytest tests/test_contact_and_settings.py -v` — Expected: all PASS.
Run: `pytest tests/ -v` — Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "Add contact form, admin messages inbox, and site settings endpoints"
```

---

### Task 11: Manual smoke run against real MongoDB

**Files:**
- Create: `backend/README.md`

- [ ] **Step 1: Start Mongo**

Run (repo root): `docker compose -f docker-compose.dev.yml up -d`
Expected: mongo container running (`docker ps` shows it).

- [ ] **Step 2: Seed admin and start the API**

Run (from `backend/`, venv active): `python scripts/seed_admin.py admin@covareli.ro 'parola-temporara-123'`
Expected: `Created admin admin@covareli.ro`.

Run: `uvicorn app.main:app --reload --port 8000` (leave running in background)

- [ ] **Step 3: Smoke-test with curl**

```bash
curl -s http://localhost:8000/api/health
curl -s -c /tmp/cj -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@covareli.ro","password":"parola-temporara-123"}'
curl -s -b /tmp/cj -X POST http://localhost:8000/api/admin/locations -H 'Content-Type: application/json' -d '{"name":{"ro":"Sediu Baciu","en":"Baciu Office"},"address":"Str. Jupiter 1/12","fee":0,"sort_order":1}'
curl -s http://localhost:8000/api/locations
```

Expected: health ok; login returns email; location created; public list shows it.

- [ ] **Step 4: Write `backend/README.md`**

```markdown
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
```

- [ ] **Step 5: Stop uvicorn, run the full test suite once more, commit**

Run: `pytest tests/ -v` — Expected: all PASS.

```bash
git add -A
git commit -m "Add backend README and verify smoke run against real MongoDB"
```

---

## Out of Scope for Plan 1 (delivered in later plans)

- **Plan 2:** Booking creation endpoint, Netopia v2 payment init + IPN webhook, slot-hold integration in checkout, SMTP email module (booking confirmations + contact form notification), booking admin endpoints (list/filter/status transitions/calendar data).
- **Plan 3:** Next.js public site (i18n RO/EN, all pages, SEO).
- **Plan 4:** Admin dashboard UI.
- **Plan 5:** Production docker-compose (nginx + certbot + frontend + backend + mongo), VPS deploy, mongodump cron, staging, DNS cutover.
