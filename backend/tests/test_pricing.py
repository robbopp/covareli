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
