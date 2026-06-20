# Booking, Netopia & Email — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add public booking creation with Netopia v2 payment initiation, IPN webhook verification, SMTP email notifications on payment, and admin booking management to the existing FastAPI backend.

**Architecture:** Public `POST /api/bookings` validates availability + price server-side, creates a `pending_payment` booking, calls Netopia v2 `/payment/card/start`, and returns a redirect URL. Netopia POSTs IPN to `POST /api/netopia/ipn`; the handler verifies authenticity by calling `GET /payment/card/{ntpID}/status` on the Netopia API, then updates booking to `paid` and sends SMTP emails via `asyncio.to_thread`. Admin endpoints list/detail/transition bookings. All existing tests must continue to pass.

**Tech Stack:** FastAPI, Beanie ≥1.26 / Motor, Netopia Payments v2 REST API via `httpx` (already in requirements), `smtplib` + `asyncio.to_thread` for email, `pytest` + `mongomock-motor` + `unittest.mock`.

---

## Files Created / Modified

**Created:**
- `backend/app/netopia.py` — `init_payment()`, `get_payment_status()` (Netopia v2 HTTP calls)
- `backend/app/email_service.py` — async `send_booking_confirmation()`, `send_admin_booking_notification()`
- `backend/app/routers/bookings.py` — `POST /api/bookings`, `GET /api/bookings/{id}/status`
- `backend/app/routers/netopia_ipn.py` — `POST /api/netopia/ipn`
- `backend/app/routers/admin_bookings.py` — `GET /api/admin/bookings`, `GET /api/admin/bookings/{id}`, `PATCH /api/admin/bookings/{id}`
- `backend/tests/test_email_service.py`
- `backend/tests/test_bookings_public.py`
- `backend/tests/test_netopia_ipn.py`
- `backend/tests/test_bookings_admin.py`
- `backend/.env.example`

**Modified:**
- `backend/app/config.py` — add Netopia + SMTP + URL env vars
- `backend/app/models/settings_doc.py` — race-safe `get_singleton` via `$setOnInsert` upsert
- `backend/app/main.py` — register 3 new routers

---

## Task 1: Config additions + SiteSettings race fix

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/models/settings_doc.py`
- Create: `backend/.env.example`

- [ ] **Step 1: Write the failing test for SiteSettings race**

Create `backend/tests/test_settings_singleton.py`:

```python
import pytest

from app.models.settings_doc import SiteSettings


async def test_get_singleton_is_idempotent(db):
    """Calling get_singleton twice must not create duplicate documents."""
    s1 = await SiteSettings.get_singleton()
    s2 = await SiteSettings.get_singleton()
    assert str(s1.id) == str(s2.id)
    count = await SiteSettings.count()
    assert count == 1


async def test_get_singleton_returns_defaults(db):
    s = await SiteSettings.get_singleton()
    assert s.contact_email == "office@covareli.ro"
    assert s.payment_mode.value == "full"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_settings_singleton.py -v
```

Expected: PASS (the current implementation already passes the idempotency test in a single-threaded test environment — but the race-safe version is required for production). If the tests pass, proceed to fix the implementation anyway because the current `get_singleton` is not race-safe under concurrency.

- [ ] **Step 3: Update config.py**

Replace the full content of `backend/app/config.py`:

```python
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
    netopia_signature: str = ""   # POS Signature from Netopia dashboard
    netopia_api_key: str = ""     # API Key from Netopia dashboard
    netopia_sandbox: bool = True  # False in production

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@covareli.ro"

    # Public URLs (used in Netopia redirect + IPN URLs)
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    @model_validator(mode="after")
    def _warn_short_jwt_secret(self):
        if len(self.jwt_secret.encode()) < 32:
            warnings.warn(
                "jwt_secret is shorter than 32 bytes; set a 32+ byte JWT_SECRET before production deploy."
            )
        return self


config = AppConfig()
```

- [ ] **Step 4: Fix SiteSettings.get_singleton() — race-safe upsert**

Replace the `get_singleton` method in `backend/app/models/settings_doc.py`:

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
        defaults = cls()
        doc = defaults.model_dump(exclude={"id", "revision_id"})
        await cls.get_motor_collection().update_one(
            {}, {"$setOnInsert": doc}, upsert=True
        )
        return await cls.find_one({})
```

- [ ] **Step 5: Create .env.example**

Create `backend/.env.example`:

```
# MongoDB
MONGO_URL=mongodb://mongo:27017
MONGO_DB=covareli

# JWT
JWT_SECRET=change-me-to-a-32-plus-byte-random-string
JWT_EXPIRES_HOURS=12
COOKIE_SECURE=true

# Media
MEDIA_DIR=media

# Netopia Payments v2
NETOPIA_SIGNATURE=XXXX-XXXX-XXXX-XXXX-XXXX
NETOPIA_API_KEY=your-netopia-api-key
NETOPIA_SANDBOX=true

# SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=office@covareli.ro
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=office@covareli.ro

# Public URLs (no trailing slash)
FRONTEND_URL=https://covareli.ro
BACKEND_URL=https://covareli.ro
```

- [ ] **Step 6: Run all existing tests to verify nothing broke**

```bash
cd backend && . .venv/bin/activate && pytest tests/ -v
```

Expected: all tests pass (63 + 2 new = 65).

- [ ] **Step 7: Commit**

```bash
cd backend && git add app/config.py app/models/settings_doc.py .env.example tests/test_settings_singleton.py && git commit -m "feat: add Netopia/SMTP config vars and race-safe SiteSettings singleton"
```

---

## Task 2: Netopia v2 API client

**Files:**
- Create: `backend/app/netopia.py`
- Create: `backend/tests/test_netopia_client.py`

Netopia v2 reference:
- Sandbox base: `https://secure.sandbox.netopia-payments.com`
- Prod base: `https://secure.netopia-payments.com`
- Auth: `Authorization: {api_key}` header (no "Bearer" prefix)
- Init payment: `POST /payment/card/start` → response `payment.paymentURL` + `payment.ntpID`
- Status poll: `GET /payment/card/{ntpID}/status` → response `payment.status` (int), `payment.orderID`
- Paid statuses: `3` (Authorized) and `5` (Confirmed)

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_netopia_client.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import app.netopia as netopia_module
from app.netopia import PAID_STATUSES, get_payment_status, init_payment


@pytest.fixture(autouse=True)
def reset_config(monkeypatch):
    monkeypatch.setattr("app.netopia.config.netopia_sandbox", True)
    monkeypatch.setattr("app.netopia.config.netopia_signature", "TEST-SIG-1234")
    monkeypatch.setattr("app.netopia.config.netopia_api_key", "test-api-key")
    monkeypatch.setattr("app.netopia.config.frontend_url", "http://localhost:3000")
    monkeypatch.setattr("app.netopia.config.backend_url", "http://localhost:8000")


async def test_init_payment_returns_url_and_ntp_id():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "payment": {"paymentURL": "https://sandbox.netopia.com/pay/abc", "ntpID": "NTP001"}
    }
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.netopia.httpx.AsyncClient", return_value=mock_client):
        result = await init_payment(
            booking_id="abc123",
            amount_ron=500,
            customer_name="Ion Popescu",
            customer_email="ion@example.com",
            customer_phone="0721000000",
            description="Rezervare Dacia Logan",
        )

    assert result["payment_url"] == "https://sandbox.netopia.com/pay/abc"
    assert result["ntp_id"] == "NTP001"
    _, kwargs = mock_client.post.call_args
    body = kwargs["json"]
    assert body["order"]["orderID"] == "abc123"
    assert body["order"]["amount"] == 500
    assert body["order"]["posSignature"] == "TEST-SIG-1234"
    assert body["config"]["confirmUrl"] == "http://localhost:8000/api/netopia/ipn"
    assert body["order"]["billing"]["firstName"] == "Ion"
    assert body["order"]["billing"]["lastName"] == "Popescu"


async def test_init_payment_single_name_word():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "payment": {"paymentURL": "https://sandbox.netopia.com/pay/xyz", "ntpID": "NTP002"}
    }
    mock_resp.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.netopia.httpx.AsyncClient", return_value=mock_client):
        result = await init_payment("b2", 100, "Maria", "maria@x.com", "0700", "Test")

    _, kwargs = mock_client.post.call_args
    assert kwargs["json"]["order"]["billing"]["firstName"] == "Maria"
    assert kwargs["json"]["order"]["billing"]["lastName"] == "-"


async def test_get_payment_status_returns_status_and_order_id():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "payment": {"status": 3, "orderID": "booking123", "amount": 500.0}
    }
    mock_resp.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.netopia.httpx.AsyncClient", return_value=mock_client):
        result = await get_payment_status("NTP001")

    assert result["status"] == 3
    assert result["order_id"] == "booking123"
    assert result["amount"] == 500.0
    _, kwargs = mock_client.get.call_args
    assert "NTP001" in kwargs.get("url", mock_client.get.call_args[0][0] if mock_client.get.call_args[0] else "")


def test_paid_statuses_include_authorized_and_confirmed():
    assert 3 in PAID_STATUSES
    assert 5 in PAID_STATUSES
    assert 2 not in PAID_STATUSES
    assert 6 not in PAID_STATUSES
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_netopia_client.py -v
```

Expected: ImportError or ModuleNotFoundError — `app.netopia` does not exist yet.

- [ ] **Step 3: Create `backend/app/netopia.py`**

```python
from datetime import datetime, timezone

import httpx

from app.config import config

SANDBOX_BASE = "https://secure.sandbox.netopia-payments.com"
PROD_BASE = "https://secure.netopia-payments.com"

PAID_STATUSES: frozenset[int] = frozenset({3, 5})


def _base() -> str:
    return SANDBOX_BASE if config.netopia_sandbox else PROD_BASE


async def init_payment(
    booking_id: str,
    amount_ron: int,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    description: str,
) -> dict:
    """
    Initiate a Netopia v2 card payment.
    Returns {"payment_url": str, "ntp_id": str}.
    Raises httpx.HTTPStatusError on API error.
    """
    parts = customer_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else "-"

    billing = {
        "email": customer_email,
        "phone": customer_phone,
        "firstName": first_name,
        "lastName": last_name,
        "city": "Cluj-Napoca",
        "country": 642,
        "state": "CJ",
        "postalCode": "400001",
        "details": "",
    }
    payload = {
        "config": {
            "emailTemplate": "",
            "emailSubject": "",
            "cancelUrl": f"{config.frontend_url}/rezervare?status=cancelled&booking={booking_id}",
            "confirmUrl": f"{config.backend_url}/api/netopia/ipn",
            "language": "ro",
        },
        "payment": {
            "options": {"installments": 0, "bonus": 0},
            "instrument": {"type": "card"},
            "data": {},
        },
        "order": {
            "ntpID": "",
            "posSignature": config.netopia_signature,
            "dateTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "description": description,
            "orderID": booking_id,
            "amount": float(amount_ron),
            "currency": "RON",
            "billing": billing,
            "shipping": billing,
            "products": [
                {
                    "name": description,
                    "code": booking_id,
                    "category": "rent-a-car",
                    "price": float(amount_ron),
                    "vat": 0,
                }
            ],
            "installments": {"selected": 0, "available": [0]},
            "data": {},
        },
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{_base()}/payment/card/start",
            json=payload,
            headers={"Authorization": config.netopia_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    payment = data.get("payment", {})
    return {
        "payment_url": payment["paymentURL"],
        "ntp_id": payment.get("ntpID", ""),
    }


async def get_payment_status(ntp_id: str) -> dict:
    """
    Fetch authoritative payment status from Netopia by ntpID.
    Returns {"status": int, "order_id": str, "amount": float}.
    Raises httpx.HTTPStatusError on API error.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{_base()}/payment/card/{ntp_id}/status",
            headers={"Authorization": config.netopia_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    payment = data.get("payment", {})
    return {
        "status": payment.get("status", -1),
        "order_id": payment.get("orderID", ""),
        "amount": float(payment.get("amount", 0)),
    }
```

- [ ] **Step 4: Fix the `get_payment_status` URL assertion in the test**

The test checks that the URL contains `NTP001`. The actual call is `client.get(f"{_base()}/payment/card/{ntp_id}/status", ...)`. The positional arg is the URL. Update the test assertion:

```python
    url_called = mock_client.get.call_args[0][0]
    assert "NTP001" in url_called
```

Replace the last two assertion lines in `test_get_payment_status_returns_status_and_order_id` with:

```python
    url_called = mock_client.get.call_args[0][0]
    assert "NTP001" in url_called
```

Edit `backend/tests/test_netopia_client.py` — replace:
```python
    _, kwargs = mock_client.get.call_args
    assert "NTP001" in kwargs.get("url", mock_client.get.call_args[0][0] if mock_client.get.call_args[0] else "")
```
with:
```python
    url_called = mock_client.get.call_args[0][0]
    assert "NTP001" in url_called
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_netopia_client.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
cd backend && git add app/netopia.py tests/test_netopia_client.py && git commit -m "feat: add Netopia v2 API client with init_payment and get_payment_status"
```

---

## Task 3: Email service

**Files:**
- Create: `backend/app/email_service.py`
- Create: `backend/tests/test_email_service.py`

Email sends run via `asyncio.to_thread` to avoid blocking the event loop with synchronous `smtplib`. When `SMTP_HOST` is empty (dev/test default), all sends are silent no-ops.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_email_service.py`:

```python
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.email_service import send_admin_booking_notification, send_booking_confirmation


async def test_send_booking_confirmation_noop_when_no_smtp_host(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_host", "")
    with patch("app.email_service.smtplib.SMTP") as mock_smtp:
        await send_booking_confirmation(
            customer_email="ion@example.com",
            customer_name="Ion Pop",
            booking_id="abc123",
            car_name="Dacia Logan",
            pickup_at="2025-07-10T10:00:00",
            dropoff_at="2025-07-12T10:00:00",
            total_ron=500,
        )
    mock_smtp.assert_not_called()


async def test_send_booking_confirmation_sends_email(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_host", "smtp.example.com")
    monkeypatch.setattr("app.email_service.config.smtp_port", 587)
    monkeypatch.setattr("app.email_service.config.smtp_user", "user@example.com")
    monkeypatch.setattr("app.email_service.config.smtp_password", "secret")
    monkeypatch.setattr("app.email_service.config.smtp_from", "noreply@covareli.ro")

    mock_server = MagicMock()
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch("app.email_service.smtplib.SMTP", return_value=mock_server):
        await send_booking_confirmation(
            customer_email="ion@example.com",
            customer_name="Ion Pop",
            booking_id="abc123",
            car_name="Dacia Logan",
            pickup_at="2025-07-10T10:00:00",
            dropoff_at="2025-07-12T10:00:00",
            total_ron=500,
        )

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "secret")
    assert mock_server.sendmail.called
    to_addr = mock_server.sendmail.call_args[0][1]
    assert to_addr == "ion@example.com"
    msg_str = mock_server.sendmail.call_args[0][2]
    assert "Ion Pop" in msg_str
    assert "Dacia Logan" in msg_str
    assert "500" in msg_str


async def test_send_admin_notification_noop_when_no_smtp_host(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_host", "")
    with patch("app.email_service.smtplib.SMTP") as mock_smtp:
        await send_admin_booking_notification(
            customer_name="Ion Pop",
            customer_email="ion@example.com",
            customer_phone="0721000000",
            booking_id="abc123",
            car_name="Dacia Logan",
            pickup_at="2025-07-10T10:00:00",
            dropoff_at="2025-07-12T10:00:00",
            total_ron=500,
            admin_email="office@covareli.ro",
        )
    mock_smtp.assert_not_called()


async def test_send_admin_notification_sends_to_admin(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_host", "smtp.example.com")
    monkeypatch.setattr("app.email_service.config.smtp_port", 587)
    monkeypatch.setattr("app.email_service.config.smtp_user", "")
    monkeypatch.setattr("app.email_service.config.smtp_from", "noreply@covareli.ro")

    mock_server = MagicMock()
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch("app.email_service.smtplib.SMTP", return_value=mock_server):
        await send_admin_booking_notification(
            customer_name="Ion Pop",
            customer_email="ion@example.com",
            customer_phone="0721000000",
            booking_id="abc123",
            car_name="Dacia Logan",
            pickup_at="2025-07-10T10:00:00",
            dropoff_at="2025-07-12T10:00:00",
            total_ron=500,
            admin_email="office@covareli.ro",
        )

    assert mock_server.sendmail.called
    to_addr = mock_server.sendmail.call_args[0][1]
    assert to_addr == "office@covareli.ro"
    mock_server.login.assert_not_called()  # smtp_user is empty
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_email_service.py -v
```

Expected: ImportError — `app.email_service` does not exist yet.

- [ ] **Step 3: Create `backend/app/email_service.py`**

```python
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import config


def _smtp_send(to: str, subject: str, body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.smtp_from
    msg["To"] = to
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10) as server:
        server.starttls()
        if config.smtp_user:
            server.login(config.smtp_user, config.smtp_password)
        server.sendmail(config.smtp_from, to, msg.as_string())


async def send_booking_confirmation(
    customer_email: str,
    customer_name: str,
    booking_id: str,
    car_name: str,
    pickup_at: str,
    dropoff_at: str,
    total_ron: int,
) -> None:
    if not config.smtp_host:
        return
    subject = f"Confirmare rezervare Covareli #{booking_id[:8]}"
    body = (
        f"Buna ziua {customer_name},\n\n"
        f"Rezervarea dumneavoastra a fost platita cu succes.\n\n"
        f"Masina: {car_name}\n"
        f"Preluare: {pickup_at}\n"
        f"Returnare: {dropoff_at}\n"
        f"Total achitat: {total_ron} RON\n\n"
        f"Va asteptam!\n"
        f"Echipa Covareli\n"
        f"office@covareli.ro | +40 749 323 172"
    )
    await asyncio.to_thread(_smtp_send, customer_email, subject, body)


async def send_admin_booking_notification(
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    booking_id: str,
    car_name: str,
    pickup_at: str,
    dropoff_at: str,
    total_ron: int,
    admin_email: str,
) -> None:
    if not config.smtp_host:
        return
    subject = f"Rezervare noua #{booking_id[:8]} — {car_name}"
    body = (
        f"Rezervare noua platita.\n\n"
        f"Client: {customer_name}\n"
        f"Email: {customer_email}\n"
        f"Telefon: {customer_phone}\n\n"
        f"Masina: {car_name}\n"
        f"Preluare: {pickup_at}\n"
        f"Returnare: {dropoff_at}\n"
        f"Total: {total_ron} RON\n\n"
        f"ID rezervare: {booking_id}"
    )
    await asyncio.to_thread(_smtp_send, admin_email, subject, body)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_email_service.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd backend && git add app/email_service.py tests/test_email_service.py && git commit -m "feat: add async SMTP email service for booking confirmation and admin notification"
```

---

## Task 4: Public booking creation + status endpoints

**Files:**
- Create: `backend/app/routers/bookings.py`
- Create: `backend/tests/test_bookings_public.py`

`POST /api/bookings` — server-side validates availability + price, creates `pending_payment` booking, calls `init_payment`, saves `netopia_ref`, returns `{booking_id, payment_url, price}`.
`GET /api/bookings/{booking_id}/status` — public status poll for the return-from-payment page.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_bookings_public.py`:

```python
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.auth.security import hash_password
from app.models import AdminUser, Booking, BookingStatus, Car, Location
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission


@pytest_asyncio.fixture
async def car(db):
    c = Car(
        brand="Dacia", model="Logan", year=2020,
        body_type=BodyType.sedan, fuel=FuelType.petrol,
        transmission=Transmission.manual, seats=5, doors=4,
        price_tiers=[
            PriceTier(min_days=1, max_days=2, price_per_day=200),
            PriceTier(min_days=3, price_per_day=170),
        ],
        slug="dacia-logan-test-booking",
    )
    await c.insert()
    return c


@pytest_asyncio.fixture
async def loc(db):
    l = Location(name=LocalizedStr(ro="Aeroport", en="Airport"), fee=50)
    await l.insert()
    return l


VALID_BODY = None  # filled per test using car/loc ids


async def test_create_booking_happy_path(api, car, loc):
    body = {
        "car_id": str(car.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-10T10:00:00",
        "dropoff_at": "2025-07-12T10:00:00",  # 2 days
        "pickup_location_id": str(loc.id),
        "dropoff_location_id": str(loc.id),
    }
    with patch("app.routers.bookings.init_payment", new_callable=AsyncMock) as mock_pay:
        mock_pay.return_value = {
            "payment_url": "https://sandbox.netopia.com/pay/TEST",
            "ntp_id": "NTP_TEST_001",
        }
        resp = await api.post("/api/bookings", json=body)

    assert resp.status_code == 201
    data = resp.json()
    assert "booking_id" in data
    assert data["payment_url"] == "https://sandbox.netopia.com/pay/TEST"
    assert data["price"]["days"] == 2
    assert data["price"]["price_per_day"] == 200
    assert data["price"]["pickup_fee"] == 50
    assert data["price"]["dropoff_fee"] == 50
    assert data["price"]["total"] == 500  # 2*200 + 50 + 50

    # Booking stored with netopia_ref
    from beanie import PydanticObjectId
    booking = await Booking.get(PydanticObjectId(data["booking_id"]))
    assert booking is not None
    assert booking.status == BookingStatus.pending_payment
    assert booking.netopia_ref == "NTP_TEST_001"

    # init_payment called with correct amount
    mock_pay.assert_called_once()
    call_kwargs = mock_pay.call_args[1]
    assert call_kwargs["amount_ron"] == 500
    assert call_kwargs["customer_email"] == "ion@example.com"


async def test_create_booking_car_not_found(api, loc):
    body = {
        "car_id": "000000000000000000000001",
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-10T10:00:00",
        "dropoff_at": "2025-07-12T10:00:00",
        "pickup_location_id": "000000000000000000000002",
        "dropoff_location_id": "000000000000000000000002",
    }
    resp = await api.post("/api/bookings", json=body)
    assert resp.status_code == 404


async def test_create_booking_dropoff_before_pickup(api, car, loc):
    body = {
        "car_id": str(car.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-12T10:00:00",
        "dropoff_at": "2025-07-10T10:00:00",
        "pickup_location_id": str(loc.id),
        "dropoff_location_id": str(loc.id),
    }
    resp = await api.post("/api/bookings", json=body)
    assert resp.status_code == 422


async def test_create_booking_unavailable_car(api, car, loc):
    from app.models import Customer, PriceBreakdown
    # Insert an existing paid booking that blocks the same dates
    existing = Booking(
        car_id=car.id,
        customer=Customer(name="Alt Client", email="alt@x.com", phone="0700"),
        pickup_at=datetime(2025, 7, 10, 10, 0),
        dropoff_at=datetime(2025, 7, 12, 10, 0),
        pickup_location_id=loc.id,
        dropoff_location_id=loc.id,
        price=PriceBreakdown(days=2, price_per_day=200, car_total=400, pickup_fee=50, dropoff_fee=50, total=500),
        status=BookingStatus.paid,
    )
    await existing.insert()

    body = {
        "car_id": str(car.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-11T10:00:00",
        "dropoff_at": "2025-07-13T10:00:00",
        "pickup_location_id": str(loc.id),
        "dropoff_location_id": str(loc.id),
    }
    resp = await api.post("/api/bookings", json=body)
    assert resp.status_code == 409


async def test_create_booking_netopia_failure_returns_502(api, car, loc):
    body = {
        "car_id": str(car.id),
        "customer_name": "Ion Popescu",
        "customer_email": "ion@example.com",
        "customer_phone": "0721000000",
        "pickup_at": "2025-07-10T10:00:00",
        "dropoff_at": "2025-07-12T10:00:00",
        "pickup_location_id": str(loc.id),
        "dropoff_location_id": str(loc.id),
    }
    with patch("app.routers.bookings.init_payment", new_callable=AsyncMock) as mock_pay:
        mock_pay.side_effect = Exception("Netopia down")
        resp = await api.post("/api/bookings", json=body)

    assert resp.status_code == 502


async def test_booking_status_returns_status(api, car, loc):
    from app.models import Customer, PriceBreakdown
    booking = Booking(
        car_id=car.id,
        customer=Customer(name="Ion Pop", email="ion@x.com", phone="0721"),
        pickup_at=datetime(2025, 7, 10, 10, 0),
        dropoff_at=datetime(2025, 7, 12, 10, 0),
        pickup_location_id=loc.id,
        dropoff_location_id=loc.id,
        price=PriceBreakdown(days=2, price_per_day=200, car_total=400, pickup_fee=0, dropoff_fee=0, total=400),
        status=BookingStatus.paid,
    )
    await booking.insert()

    resp = await api.get(f"/api/bookings/{booking.id}/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"
    assert resp.json()["booking_id"] == str(booking.id)


async def test_booking_status_not_found(api, db):
    resp = await api.get("/api/bookings/000000000000000000000099/status")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_bookings_public.py -v
```

Expected: errors because `app.routers.bookings` does not exist.

- [ ] **Step 3: Create `backend/app/routers/bookings.py`**

```python
import logging

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.availability import car_is_available
from app.models import Booking, BookingStatus, Car, Customer, Location, PriceBreakdown
from app.netopia import init_payment
from app.pricing import quote_total

router = APIRouter(prefix="/api", tags=["bookings"])
logger = logging.getLogger(__name__)


class BookingRequest(BaseModel):
    car_id: str
    customer_name: str = Field(min_length=2, max_length=200)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=4, max_length=30)
    pickup_at: str
    dropoff_at: str
    pickup_location_id: str
    dropoff_location_id: str


@router.post("/bookings", status_code=201)
async def create_booking(body: BookingRequest):
    from datetime import datetime

    try:
        pickup_dt = datetime.fromisoformat(body.pickup_at)
        dropoff_dt = datetime.fromisoformat(body.dropoff_at)
    except ValueError:
        raise HTTPException(422, "Invalid datetime format; use ISO 8601")

    if dropoff_dt <= pickup_dt:
        raise HTTPException(422, "'dropoff_at' must be after 'pickup_at'")

    try:
        car_oid = PydanticObjectId(body.car_id)
    except Exception:
        raise HTTPException(422, "invalid car_id")

    car = await Car.find_one(Car.id == car_oid, Car.active == True)  # noqa: E712
    if car is None:
        raise HTTPException(404, "Car not found")

    try:
        pickup_loc_oid = PydanticObjectId(body.pickup_location_id)
        dropoff_loc_oid = PydanticObjectId(body.dropoff_location_id)
    except Exception:
        raise HTTPException(422, "invalid location_id")

    pickup_loc = await Location.find_one(Location.id == pickup_loc_oid, Location.active == True)  # noqa: E712
    dropoff_loc = await Location.find_one(Location.id == dropoff_loc_oid, Location.active == True)  # noqa: E712
    if pickup_loc is None or dropoff_loc is None:
        raise HTTPException(404, "Location not found")

    available = await car_is_available(car_oid, pickup_dt, dropoff_dt)
    if not available:
        raise HTTPException(409, "Car not available for selected dates")

    price = quote_total(
        car.price_tiers,
        pickup_dt,
        dropoff_dt,
        pickup_fee=pickup_loc.fee,
        dropoff_fee=dropoff_loc.fee,
    )

    booking = Booking(
        car_id=car_oid,
        customer=Customer(
            name=body.customer_name,
            email=body.customer_email,
            phone=body.customer_phone,
        ),
        pickup_at=pickup_dt,
        dropoff_at=dropoff_dt,
        pickup_location_id=pickup_loc_oid,
        dropoff_location_id=dropoff_loc_oid,
        price=price,
    )
    await booking.insert()

    try:
        netopia = await init_payment(
            booking_id=str(booking.id),
            amount_ron=price.total,
            customer_name=body.customer_name,
            customer_email=body.customer_email,
            customer_phone=body.customer_phone,
            description=f"Rezervare {car.brand} {car.model} #{str(booking.id)[:8]}",
        )
    except Exception as exc:
        logger.error("Netopia init_payment failed for booking %s: %s", booking.id, exc)
        raise HTTPException(502, "Payment provider unavailable")

    booking.netopia_ref = netopia["ntp_id"]
    await booking.save()

    return {
        "booking_id": str(booking.id),
        "payment_url": netopia["payment_url"],
        "price": price.model_dump(),
    }


@router.get("/bookings/{booking_id}/status")
async def booking_status(booking_id: str):
    try:
        oid = PydanticObjectId(booking_id)
    except Exception:
        raise HTTPException(422, "invalid booking_id")
    booking = await Booking.get(oid)
    if booking is None:
        raise HTTPException(404, "Booking not found")
    return {"status": booking.status, "booking_id": booking_id}
```

- [ ] **Step 4: Register router in main.py (temporary, just for test wiring)**

Add to `backend/app/main.py` (full wiring will be done in Task 7; for now just ensure the import works):

Skip this step — the router will be registered in Task 7. For tests, `app/main.py` must import the router. Add the import and `include_router` call now:

In `backend/app/main.py`, add after the existing router imports:

```python
from app.routers.bookings import router as bookings_router
```

And add after `app.include_router(public_router)`:

```python
app.include_router(bookings_router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_bookings_public.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 6: Run full test suite to verify no regressions**

```bash
cd backend && . .venv/bin/activate && pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
cd backend && git add app/routers/bookings.py app/main.py tests/test_bookings_public.py && git commit -m "feat: add public booking creation with Netopia payment initiation and status endpoint"
```

---

## Task 5: Netopia IPN webhook handler

**Files:**
- Create: `backend/app/routers/netopia_ipn.py`
- Create: `backend/tests/test_netopia_ipn.py`

The IPN handler:
1. Extracts `payment.ntpID` and `payment.orderID` from Netopia's POST body.
2. Verifies by calling `get_payment_status(ntp_id)` — compares `order_id` from API response with IPN body.
3. If Netopia status is in `PAID_STATUSES` (3 or 5) and booking is `pending_payment` → sets status to `paid`, sends emails.
4. If status indicates failure/cancellation and booking is `pending_payment` → sets status to `cancelled`.
5. Always returns `{"code": "0", "message": "ok"}` with HTTP 200 — Netopia requires 200 or it retries.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_netopia_ipn.py`:

```python
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.models import Booking, BookingStatus, Car, Location
from app.models.booking import Customer, PriceBreakdown
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission


@pytest_asyncio.fixture
async def car(db):
    c = Car(
        brand="Dacia", model="Logan", year=2020,
        body_type=BodyType.sedan, fuel=FuelType.petrol,
        transmission=Transmission.manual, seats=5, doors=4,
        price_tiers=[PriceTier(min_days=1, price_per_day=200)],
        slug="dacia-logan-ipn-test",
    )
    await c.insert()
    return c


@pytest_asyncio.fixture
async def loc(db):
    l = Location(name=LocalizedStr(ro="Cluj", en="Cluj"), fee=0)
    await l.insert()
    return l


@pytest_asyncio.fixture
async def pending_booking(car, loc):
    b = Booking(
        car_id=car.id,
        customer=Customer(name="Ion Pop", email="ion@example.com", phone="0721000000"),
        pickup_at=datetime(2025, 7, 10, 10, 0),
        dropoff_at=datetime(2025, 7, 12, 10, 0),
        pickup_location_id=loc.id,
        dropoff_location_id=loc.id,
        price=PriceBreakdown(days=2, price_per_day=200, car_total=400, pickup_fee=0, dropoff_fee=0, total=400),
        status=BookingStatus.pending_payment,
        netopia_ref="NTP_TEST_001",
    )
    await b.insert()
    return b


async def test_ipn_paid_status_transitions_booking_to_paid(api, pending_booking):
    with patch("app.routers.netopia_ipn.get_payment_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {
            "status": 3,
            "order_id": str(pending_booking.id),
            "amount": 400.0,
        }
        with patch("app.routers.netopia_ipn.send_booking_confirmation", new_callable=AsyncMock):
            with patch("app.routers.netopia_ipn.send_admin_booking_notification", new_callable=AsyncMock):
                resp = await api.post("/api/netopia/ipn", json={
                    "payment": {
                        "ntpID": "NTP_TEST_001",
                        "status": 3,
                        "amount": 400.0,
                        "currency": "RON",
                        "orderID": str(pending_booking.id),
                    }
                })

    assert resp.status_code == 200
    assert resp.json()["code"] == "0"
    updated = await Booking.get(pending_booking.id)
    assert updated.status == BookingStatus.paid


async def test_ipn_paid_sends_emails(api, pending_booking):
    with patch("app.routers.netopia_ipn.get_payment_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {
            "status": 3,
            "order_id": str(pending_booking.id),
            "amount": 400.0,
        }
        with patch("app.routers.netopia_ipn.send_booking_confirmation", new_callable=AsyncMock) as mock_confirm:
            with patch("app.routers.netopia_ipn.send_admin_booking_notification", new_callable=AsyncMock) as mock_admin:
                await api.post("/api/netopia/ipn", json={
                    "payment": {
                        "ntpID": "NTP_TEST_001",
                        "status": 3,
                        "amount": 400.0,
                        "currency": "RON",
                        "orderID": str(pending_booking.id),
                    }
                })

    mock_confirm.assert_called_once()
    mock_admin.assert_called_once()
    confirm_kwargs = mock_confirm.call_args[1]
    assert confirm_kwargs["customer_email"] == "ion@example.com"
    assert confirm_kwargs["total_ron"] == 400


async def test_ipn_already_paid_is_idempotent(api, pending_booking):
    """Second IPN with paid status must not send duplicate emails."""
    pending_booking.status = BookingStatus.paid
    await pending_booking.save()

    with patch("app.routers.netopia_ipn.get_payment_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {
            "status": 3,
            "order_id": str(pending_booking.id),
            "amount": 400.0,
        }
        with patch("app.routers.netopia_ipn.send_booking_confirmation", new_callable=AsyncMock) as mock_confirm:
            resp = await api.post("/api/netopia/ipn", json={
                "payment": {
                    "ntpID": "NTP_TEST_001",
                    "status": 3,
                    "amount": 400.0,
                    "currency": "RON",
                    "orderID": str(pending_booking.id),
                }
            })

    assert resp.status_code == 200
    mock_confirm.assert_not_called()


async def test_ipn_cancelled_status_cancels_pending_booking(api, pending_booking):
    with patch("app.routers.netopia_ipn.get_payment_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {
            "status": 2,
            "order_id": str(pending_booking.id),
            "amount": 0.0,
        }
        resp = await api.post("/api/netopia/ipn", json={
            "payment": {
                "ntpID": "NTP_TEST_001",
                "status": 2,
                "amount": 0.0,
                "currency": "RON",
                "orderID": str(pending_booking.id),
            }
        })

    assert resp.status_code == 200
    updated = await Booking.get(pending_booking.id)
    assert updated.status == BookingStatus.cancelled


async def test_ipn_order_id_mismatch_is_ignored(api, pending_booking):
    """If Netopia status API returns a different orderID → reject silently."""
    with patch("app.routers.netopia_ipn.get_payment_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {
            "status": 3,
            "order_id": "different-order-id",
            "amount": 400.0,
        }
        resp = await api.post("/api/netopia/ipn", json={
            "payment": {
                "ntpID": "NTP_TEST_001",
                "status": 3,
                "amount": 400.0,
                "currency": "RON",
                "orderID": str(pending_booking.id),
            }
        })

    assert resp.status_code == 200
    untouched = await Booking.get(pending_booking.id)
    assert untouched.status == BookingStatus.pending_payment


async def test_ipn_unknown_booking_returns_200(api, db):
    """IPN for a booking that doesn't exist must still return 200."""
    with patch("app.routers.netopia_ipn.get_payment_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {
            "status": 3,
            "order_id": "000000000000000000000099",
            "amount": 100.0,
        }
        resp = await api.post("/api/netopia/ipn", json={
            "payment": {
                "ntpID": "NTP_UNKNOWN",
                "status": 3,
                "amount": 100.0,
                "currency": "RON",
                "orderID": "000000000000000000000099",
            }
        })

    assert resp.status_code == 200


async def test_ipn_missing_fields_returns_200(api, db):
    """Malformed IPN body must not crash; always return 200."""
    resp = await api.post("/api/netopia/ipn", json={"unexpected": "garbage"})
    assert resp.status_code == 200
    assert resp.json()["code"] == "0"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_netopia_ipn.py -v
```

Expected: errors because `app.routers.netopia_ipn` does not exist.

- [ ] **Step 3: Create `backend/app/routers/netopia_ipn.py`**

```python
import logging

from beanie import PydanticObjectId
from fastapi import APIRouter, Request

from app.email_service import send_admin_booking_notification, send_booking_confirmation
from app.models import Booking, BookingStatus, Car, SiteSettings
from app.netopia import PAID_STATUSES, get_payment_status

router = APIRouter(prefix="/api", tags=["netopia"])
logger = logging.getLogger(__name__)


@router.post("/netopia/ipn")
async def netopia_ipn(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"code": "0", "message": "ok"}

    payment_block = body.get("payment", {})
    ntp_id = payment_block.get("ntpID", "")
    order_id = payment_block.get("orderID", "")

    if not ntp_id or not order_id:
        logger.warning("IPN missing ntpID or orderID: %s", body)
        return {"code": "0", "message": "ok"}

    try:
        status_info = await get_payment_status(ntp_id)
    except Exception as exc:
        logger.error("IPN status verification failed for ntpID=%s: %s", ntp_id, exc)
        return {"code": "0", "message": "ok"}

    if status_info["order_id"] != order_id:
        logger.warning(
            "IPN orderID mismatch: API returned %s, IPN body has %s",
            status_info["order_id"], order_id,
        )
        return {"code": "0", "message": "ok"}

    try:
        oid = PydanticObjectId(order_id)
    except Exception:
        return {"code": "0", "message": "ok"}

    booking = await Booking.get(oid)
    if booking is None:
        logger.warning("IPN for unknown booking %s", order_id)
        return {"code": "0", "message": "ok"}

    netopia_status = status_info["status"]

    if netopia_status in PAID_STATUSES:
        if booking.status == BookingStatus.pending_payment:
            booking.status = BookingStatus.paid
            await booking.save()
            await _send_booking_emails(booking)
    else:
        if booking.status == BookingStatus.pending_payment:
            booking.status = BookingStatus.cancelled
            await booking.save()

    return {"code": "0", "message": "ok"}


async def _send_booking_emails(booking: Booking) -> None:
    try:
        car = await Car.get(booking.car_id)
        car_name = f"{car.brand} {car.model}" if car else "N/A"
        settings = await SiteSettings.get_singleton()
        await send_booking_confirmation(
            customer_email=booking.customer.email,
            customer_name=booking.customer.name,
            booking_id=str(booking.id),
            car_name=car_name,
            pickup_at=booking.pickup_at.isoformat(),
            dropoff_at=booking.dropoff_at.isoformat(),
            total_ron=booking.price.total,
        )
        await send_admin_booking_notification(
            customer_name=booking.customer.name,
            customer_email=booking.customer.email,
            customer_phone=booking.customer.phone,
            booking_id=str(booking.id),
            car_name=car_name,
            pickup_at=booking.pickup_at.isoformat(),
            dropoff_at=booking.dropoff_at.isoformat(),
            total_ron=booking.price.total,
            admin_email=settings.contact_email,
        )
    except Exception as exc:
        logger.error("Failed to send emails for booking %s: %s", booking.id, exc)
```

- [ ] **Step 4: Register the IPN router in main.py**

Add to `backend/app/main.py` imports:

```python
from app.routers.netopia_ipn import router as netopia_ipn_router
```

And add after `app.include_router(bookings_router)`:

```python
app.include_router(netopia_ipn_router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_netopia_ipn.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 6: Run full test suite**

```bash
cd backend && . .venv/bin/activate && pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
cd backend && git add app/routers/netopia_ipn.py app/main.py tests/test_netopia_ipn.py && git commit -m "feat: add Netopia IPN webhook handler with payment verification and email dispatch"
```

---

## Task 6: Admin booking endpoints

**Files:**
- Create: `backend/app/routers/admin_bookings.py`
- Create: `backend/tests/test_bookings_admin.py`

Endpoints (all behind `require_admin`):
- `GET /api/admin/bookings` — list with optional filters: `status`, `car_id`, `from` (pickup ≥), `to` (pickup ≤), sorted by `-created_at`
- `GET /api/admin/bookings/{id}` — booking detail
- `PATCH /api/admin/bookings/{id}` — status transition + optional admin_notes; only these transitions are allowed:
  - `pending_payment` → `cancelled`
  - `paid` → `confirmed` or `cancelled`
  - `confirmed` → `completed` or `cancelled`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_bookings_admin.py`:

```python
from datetime import datetime

import pytest
import pytest_asyncio

from app.auth.security import hash_password
from app.models import AdminUser, Booking, BookingStatus, Car, Location
from app.models.booking import Customer, PriceBreakdown
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission


@pytest_asyncio.fixture
async def admin(api):
    await AdminUser(
        email="admin@test.ro", password_hash=hash_password("secret123")
    ).insert()
    await api.post("/api/auth/login", json={"email": "admin@test.ro", "password": "secret123"})
    return api


@pytest_asyncio.fixture
async def car(db):
    c = Car(
        brand="Dacia", model="Logan", year=2020,
        body_type=BodyType.sedan, fuel=FuelType.petrol,
        transmission=Transmission.manual, seats=5, doors=4,
        price_tiers=[PriceTier(min_days=1, price_per_day=200)],
        slug="dacia-logan-admin-booking-test",
    )
    await c.insert()
    return c


@pytest_asyncio.fixture
async def loc(db):
    l = Location(name=LocalizedStr(ro="Cluj", en="Cluj"), fee=0)
    await l.insert()
    return l


def make_booking(car, loc, status=BookingStatus.pending_payment):
    return Booking(
        car_id=car.id,
        customer=Customer(name="Ion Pop", email="ion@example.com", phone="0721"),
        pickup_at=datetime(2025, 7, 10, 10, 0),
        dropoff_at=datetime(2025, 7, 12, 10, 0),
        pickup_location_id=loc.id,
        dropoff_location_id=loc.id,
        price=PriceBreakdown(days=2, price_per_day=200, car_total=400, pickup_fee=0, dropoff_fee=0, total=400),
        status=status,
    )


async def test_list_bookings_returns_all(admin, car, loc):
    b1 = make_booking(car, loc, BookingStatus.pending_payment)
    b2 = make_booking(car, loc, BookingStatus.paid)
    await b1.insert()
    await b2.insert()

    resp = await admin.get("/api/admin/bookings")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_list_bookings_filter_by_status(admin, car, loc):
    b1 = make_booking(car, loc, BookingStatus.pending_payment)
    b2 = make_booking(car, loc, BookingStatus.paid)
    await b1.insert()
    await b2.insert()

    resp = await admin.get("/api/admin/bookings?status=paid")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "paid"


async def test_list_bookings_filter_by_car_id(admin, car, loc):
    b1 = make_booking(car, loc)
    await b1.insert()

    resp = await admin.get(f"/api/admin/bookings?car_id={car.id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp2 = await admin.get("/api/admin/bookings?car_id=000000000000000000000001")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0


async def test_get_booking_detail(admin, car, loc):
    b = make_booking(car, loc)
    await b.insert()

    resp = await admin.get(f"/api/admin/bookings/{b.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(b.id)
    assert data["customer"]["name"] == "Ion Pop"
    assert data["price"]["total"] == 400


async def test_get_booking_not_found(admin, db):
    resp = await admin.get("/api/admin/bookings/000000000000000000000099")
    assert resp.status_code == 404


async def test_transition_paid_to_confirmed(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.paid)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "confirmed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"

    updated = await Booking.get(b.id)
    assert updated.status == BookingStatus.confirmed


async def test_transition_paid_to_cancelled(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.paid)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "cancelled", "admin_notes": "Client a anulat"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    assert resp.json()["admin_notes"] == "Client a anulat"


async def test_transition_confirmed_to_completed(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.confirmed)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "completed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_invalid_transition_paid_to_completed(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.paid)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "completed"})
    assert resp.status_code == 422


async def test_invalid_transition_completed_to_cancelled(admin, car, loc):
    b = make_booking(car, loc, BookingStatus.completed)
    await b.insert()

    resp = await admin.patch(f"/api/admin/bookings/{b.id}", json={"status": "cancelled"})
    assert resp.status_code == 422


async def test_unauthenticated_access_returns_401(api, db):
    resp = await api.get("/api/admin/bookings")
    assert resp.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_bookings_admin.py -v
```

Expected: errors because `app.routers.admin_bookings` does not exist.

- [ ] **Step 3: Create `backend/app/routers/admin_bookings.py`**

```python
from datetime import datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth.deps import require_admin
from app.models import Booking, BookingStatus

router = APIRouter(
    prefix="/api/admin/bookings",
    tags=["admin-bookings"],
    dependencies=[Depends(require_admin)],
)

VALID_TRANSITIONS: dict[BookingStatus, list[BookingStatus]] = {
    BookingStatus.pending_payment: [BookingStatus.cancelled],
    BookingStatus.paid: [BookingStatus.confirmed, BookingStatus.cancelled],
    BookingStatus.confirmed: [BookingStatus.completed, BookingStatus.cancelled],
}


def serialize_booking(b: Booking) -> dict:
    data = b.model_dump(exclude={"id", "revision_id"})
    data["id"] = str(b.id)
    data["car_id"] = str(b.car_id)
    data["pickup_location_id"] = str(b.pickup_location_id)
    data["dropoff_location_id"] = str(b.dropoff_location_id)
    return data


@router.get("")
async def list_bookings(
    status: BookingStatus | None = None,
    car_id: str | None = None,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
):
    query = Booking.find()
    if status is not None:
        query = query.find(Booking.status == status)
    if car_id is not None:
        try:
            query = query.find(Booking.car_id == PydanticObjectId(car_id))
        except Exception:
            raise HTTPException(422, "invalid car_id")
    if from_ is not None:
        query = query.find(Booking.pickup_at >= from_)
    if to is not None:
        query = query.find(Booking.pickup_at <= to)
    bookings = await query.sort("-created_at").to_list()
    return [serialize_booking(b) for b in bookings]


@router.get("/{booking_id}")
async def get_booking(booking_id: str):
    try:
        oid = PydanticObjectId(booking_id)
    except Exception:
        raise HTTPException(422, "invalid booking_id")
    booking = await Booking.get(oid)
    if booking is None:
        raise HTTPException(404, "Booking not found")
    return serialize_booking(booking)


class TransitionBody(BaseModel):
    status: BookingStatus
    admin_notes: str = ""


@router.patch("/{booking_id}")
async def update_booking_status(booking_id: str, body: TransitionBody):
    try:
        oid = PydanticObjectId(booking_id)
    except Exception:
        raise HTTPException(422, "invalid booking_id")
    booking = await Booking.get(oid)
    if booking is None:
        raise HTTPException(404, "Booking not found")

    allowed = VALID_TRANSITIONS.get(booking.status, [])
    if body.status not in allowed:
        raise HTTPException(
            422,
            f"Cannot transition from '{booking.status}' to '{body.status}'",
        )

    booking.status = body.status
    if body.admin_notes:
        booking.admin_notes = body.admin_notes
    await booking.save()
    return serialize_booking(booking)
```

- [ ] **Step 4: Register the admin bookings router in main.py**

Add to `backend/app/main.py` imports:

```python
from app.routers.admin_bookings import router as admin_bookings_router
```

And add after `app.include_router(netopia_ipn_router)`:

```python
app.include_router(admin_bookings_router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && . .venv/bin/activate && pytest tests/test_bookings_admin.py -v
```

Expected: 11 tests PASS.

- [ ] **Step 6: Run full test suite**

```bash
cd backend && . .venv/bin/activate && pytest tests/ -v
```

Expected: all tests PASS (63 original + ~26 new = ~89+ total).

- [ ] **Step 7: Commit**

```bash
cd backend && git add app/routers/admin_bookings.py app/main.py tests/test_bookings_admin.py && git commit -m "feat: add admin booking list, detail, and status transition endpoints"
```

---

## Task 7: Final main.py cleanup + full verification

**Files:**
- Modify: `backend/app/main.py` (verify all 3 new routers are registered)

At this point all three routers should already be registered (each task added its own). This task verifies the final state.

- [ ] **Step 1: Verify final main.py state**

`backend/app/main.py` should read:

```python
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.config import config
from app.db import init_db
from app.routers.admin_bookings import router as admin_bookings_router
from app.routers.admin_cars import router as admin_cars_router
from app.routers.admin_locations import router as admin_locations_router
from app.routers.admin_messages import router as admin_messages_router
from app.routers.admin_settings import router as admin_settings_router
from app.routers.bookings import router as bookings_router
from app.routers.netopia_ipn import router as netopia_ipn_router
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
app.include_router(netopia_ipn_router)
app.include_router(admin_bookings_router)

Path(config.media_dir).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=config.media_dir), name="media")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

If main.py has accumulated incremental adds from Tasks 4–6, rewrite it to this clean form.

- [ ] **Step 2: Run the full test suite one final time**

```bash
cd backend && . .venv/bin/activate && pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: all tests PASS. Count should be ≥ 89.

- [ ] **Step 3: Commit if main.py was changed**

```bash
cd backend && git add app/main.py && git commit -m "refactor: clean up main.py router registration order"
```

(Skip if main.py was already in the correct final state.)

---

## Self-Review Against Spec

**Spec requirement → Task coverage:**

| Requirement | Covered by |
|---|---|
| `POST /api/bookings` — server-side price + availability validation | Task 4 |
| Creates `pending_payment` booking, returns Netopia redirect URL | Task 4 |
| Netopia IPN webhook → transitions to `paid` | Task 5 |
| IPN idempotent on duplicate notifications | Task 5 (`test_ipn_already_paid_is_idempotent`) |
| Customer confirmation email on paid | Task 5 (`_send_booking_emails`) |
| Admin notification email on paid | Task 5 (`_send_booking_emails`) |
| SMTP config via env vars | Task 1 |
| Netopia creds via env vars | Task 1 |
| Slot-hold: `pending_payment` < 30 min blocks availability | Existing `availability.py` — used by Task 4 |
| Admin: list/filter bookings | Task 6 |
| Admin: detail booking | Task 6 |
| Admin: status transitions (confirm, complete, cancel) | Task 6 |
| SiteSettings singleton race fix | Task 1 |
| Sandbox/prod Netopia toggle via env var | Task 2 (`NETOPIA_SANDBOX`) |
| `GET /api/bookings/{id}/status` for frontend polling | Task 4 |

**Placeholder scan:** No TBDs, no "similar to Task N" shortcuts, no missing code blocks.

**Type consistency:** `PriceBreakdown`, `Customer`, `Booking`, `BookingStatus` — all sourced from `app.models.booking` throughout. `PydanticObjectId` from `beanie` used consistently. `serialize_booking` in admin_bookings uses `str(b.car_id)` — matches `PydanticObjectId` field type in model.

**Out of scope (not included):** refund dashboard, advance/deposit checkout UI, per-car occupancy calendar view (calendar data is already served by `GET /api/cars/{slug}/booked-ranges` from Plan 1 — admin UI will use that in Plan 4).
