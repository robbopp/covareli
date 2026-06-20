import pytest

from app.models.settings_doc import SiteSettings


async def test_get_singleton_is_idempotent(db):
    s1 = await SiteSettings.get_singleton()
    s2 = await SiteSettings.get_singleton()
    assert str(s1.id) == str(s2.id)
    count = await SiteSettings.count()
    assert count == 1


async def test_get_singleton_returns_defaults(db):
    s = await SiteSettings.get_singleton()
    assert s.contact_email == "office@covareli.ro"
    assert s.payment_mode.value == "full"
