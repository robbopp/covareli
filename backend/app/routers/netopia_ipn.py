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
        logger.warning("IPN fara ntpID sau orderID: %s", body)
        return {"code": "0", "message": "ok"}

    try:
        status_info = await get_payment_status(ntp_id)
    except Exception as exc:
        logger.error("IPN verificare status esuat pentru ntpID=%s: %s", ntp_id, exc)
        return {"code": "0", "message": "ok"}

    if status_info["order_id"] != order_id:
        logger.warning(
            "IPN orderID mismatch: API a returnat %s, IPN body are %s",
            status_info["order_id"], order_id,
        )
        return {"code": "0", "message": "ok"}

    try:
        oid = PydanticObjectId(order_id)
    except Exception:
        return {"code": "0", "message": "ok"}

    booking = await Booking.get(oid)
    if booking is None:
        logger.warning("IPN pentru rezervare necunoscuta %s", order_id)
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
        logger.error("Eroare trimitere email pentru rezervare %s: %s", booking.id, exc)
