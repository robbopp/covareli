import math
from datetime import datetime

from app.models.booking import PriceBreakdown
from app.models.common import PriceTier
from app.timeutil import to_naive_utc


def rental_days(pickup: datetime, dropoff: datetime) -> int:
    seconds = (to_naive_utc(dropoff) - to_naive_utc(pickup)).total_seconds()
    if seconds <= 0:
        raise ValueError("dropoff must be after pickup")
    # seconds per day; safe because all datetimes are naive UTC
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
