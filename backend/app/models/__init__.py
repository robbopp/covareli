from app.models.admin_user import AdminUser
from app.models.booking import Booking, BookingStatus, Customer, PriceBreakdown
from app.models.car import Car
from app.models.common import BodyType, FuelType, LocalizedStr, PriceTier, Transmission
from app.models.contact_message import ContactMessage
from app.models.location import Location
from app.models.settings_doc import PaymentMode, SiteSettings

ALL_MODELS = [AdminUser, Booking, Car, ContactMessage, Location, SiteSettings]
