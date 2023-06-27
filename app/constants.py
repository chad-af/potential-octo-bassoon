from enum import auto

from fastapi_utils.enums import StrEnum

ADMIN_EMAIL = "admin@company.com"
ADMIN_API_KEY = "this is some test key"
API_KEY = "test api key123"
CONTACT_EMAIL = "contact@company.com"


class ChadStatus(StrEnum):
    ORDERED = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    REFUNDED = auto()
    CANCELATION_REQUESTED = auto()
    ON_HOLD = auto()
    DELIVERY_EXCEPTION = auto()
    PAYMENT_PENDING = auto()
    DELIVERY_FAILURE = auto()
