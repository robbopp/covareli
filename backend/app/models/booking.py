from datetime import datetime
from enum import Enum

import pymongo
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
        indexes = [
            pymongo.IndexModel(
                [
                    ("car_id", pymongo.ASCENDING),
                    ("pickup_at", pymongo.ASCENDING),
                    ("dropoff_at", pymongo.ASCENDING),
                ]
            ),
        ]
