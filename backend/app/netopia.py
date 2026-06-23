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
    Inițiază plată Netopia v2.
    Returnează {"payment_url": str, "ntp_id": str}.
    Aruncă httpx.HTTPStatusError la eroare API.
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
    Obține statusul plății de la Netopia prin ntpID.
    Returnează {"status": int, "order_id": str, "amount": float}.
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
