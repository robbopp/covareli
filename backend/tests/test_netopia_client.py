from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
    url_called = mock_client.get.call_args[0][0]
    assert "NTP001" in url_called


def test_paid_statuses_include_authorized_and_confirmed():
    assert 3 in PAID_STATUSES
    assert 5 in PAID_STATUSES
    assert 2 not in PAID_STATUSES
