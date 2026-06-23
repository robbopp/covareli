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
