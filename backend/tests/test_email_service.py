import base64
from unittest.mock import MagicMock, patch

import pytest

from app.email_service import send_admin_booking_notification, send_booking_confirmation


@pytest.fixture(autouse=True)
def reset_smtp_config(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_from", "noreply@covareli.ro")
    monkeypatch.setattr("app.email_service.config.smtp_port", 587)


async def test_send_booking_confirmation_noop_when_no_smtp_host(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_host", "")
    with patch("app.email_service._smtp_send") as mock_send:
        await send_booking_confirmation(
            customer_email="ion@example.com",
            customer_name="Ion Popescu",
            booking_id="abc12345",
            car_name="Dacia Logan",
            pickup_at="2025-07-10T10:00:00",
            dropoff_at="2025-07-12T10:00:00",
            total_ron=500,
        )
        mock_send.assert_not_called()


async def test_send_admin_notification_noop_when_no_smtp_host(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_host", "")
    with patch("app.email_service._smtp_send") as mock_send:
        await send_admin_booking_notification(
            customer_name="Ion Popescu",
            customer_email="ion@example.com",
            customer_phone="0721000000",
            booking_id="abc12345",
            car_name="Dacia Logan",
            pickup_at="2025-07-10T10:00:00",
            dropoff_at="2025-07-12T10:00:00",
            total_ron=500,
            admin_email="admin@covareli.ro",
        )
        mock_send.assert_not_called()


async def test_send_booking_confirmation_sends_email_when_smtp_configured(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_host", "smtp.example.com")
    monkeypatch.setattr("app.email_service.config.smtp_user", "user@example.com")
    monkeypatch.setattr("app.email_service.config.smtp_password", "secret")

    mock_server = MagicMock()
    mock_smtp_cls = MagicMock(return_value=mock_server)
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch("app.email_service.smtplib.SMTP", mock_smtp_cls):
        await send_booking_confirmation(
            customer_email="ion@example.com",
            customer_name="Ion Popescu",
            booking_id="abc12345",
            car_name="Dacia Logan",
            pickup_at="2025-07-10T10:00:00",
            dropoff_at="2025-07-12T10:00:00",
            total_ron=500,
        )

    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=10)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "secret")
    mock_server.sendmail.assert_called_once()
    # Verify recipient
    args = mock_server.sendmail.call_args[0]
    assert args[1] == "ion@example.com"
    # Verify email content includes name, car_name, total (body is base64-encoded in MIME)
    email_str = args[2]
    # Decode base64 payload from MIME message
    b64_part = email_str.split("base64\n\n")[1].split("\n\n--")[0].replace("\n", "")
    decoded = base64.b64decode(b64_part).decode("utf-8")
    assert "Ion Popescu" in decoded
    assert "Dacia Logan" in decoded
    assert "500" in decoded


async def test_send_booking_confirmation_no_login_when_smtp_user_empty(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_host", "smtp.example.com")
    monkeypatch.setattr("app.email_service.config.smtp_user", "")
    monkeypatch.setattr("app.email_service.config.smtp_password", "")

    mock_server = MagicMock()
    mock_smtp_cls = MagicMock(return_value=mock_server)
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch("app.email_service.smtplib.SMTP", mock_smtp_cls):
        await send_booking_confirmation(
            customer_email="ion@example.com",
            customer_name="Ion Popescu",
            booking_id="abc12345",
            car_name="Dacia Logan",
            pickup_at="2025-07-10T10:00:00",
            dropoff_at="2025-07-12T10:00:00",
            total_ron=500,
        )

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_not_called()


async def test_send_admin_notification_sends_email_when_smtp_configured(monkeypatch):
    monkeypatch.setattr("app.email_service.config.smtp_host", "smtp.example.com")
    monkeypatch.setattr("app.email_service.config.smtp_user", "")
    monkeypatch.setattr("app.email_service.config.smtp_password", "")

    mock_server = MagicMock()
    mock_smtp_cls = MagicMock(return_value=mock_server)
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch("app.email_service.smtplib.SMTP", mock_smtp_cls):
        await send_admin_booking_notification(
            customer_name="Ion Popescu",
            customer_email="ion@example.com",
            customer_phone="0721000000",
            booking_id="abc12345",
            car_name="Dacia Logan",
            pickup_at="2025-07-10T10:00:00",
            dropoff_at="2025-07-12T10:00:00",
            total_ron=500,
            admin_email="admin@covareli.ro",
        )

    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=10)
    mock_server.starttls.assert_called_once()
    mock_server.sendmail.assert_called_once()
    args = mock_server.sendmail.call_args[0]
    assert args[1] == "admin@covareli.ro"
    email_str = args[2]
    # Decode base64 payload from MIME message
    b64_part = email_str.split("base64\n\n")[1].split("\n\n--")[0].replace("\n", "")
    decoded = base64.b64decode(b64_part).decode("utf-8")
    assert "Ion Popescu" in decoded
    assert "Dacia Logan" in decoded
    assert "500" in decoded
