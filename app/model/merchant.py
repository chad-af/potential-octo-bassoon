from enum import Enum, auto
from typing import Optional

from fastapi_utils.enums import StrEnum
from pydantic import BaseModel


class CancellationPolicyConfig(BaseModel):
    auto_cancel_order: bool = False
    time_limit_after_placing_order: int = 10


class PendingPaymentOrderConfig(BaseModel):
    auto_cancel_order: bool = False
    time_limit_after_pending_payment: int = 3


class ReturnOrExchangeConfig(BaseModel):
    reasons: list[str] = []


class DefectiveItemsConfig(BaseModel):
    description_required: bool = True
    image_required: bool = True


class LateFromDateType(StrEnum):
    PLACED = auto()
    SHIPPED = auto()


class OrderConfig(BaseModel):
    lateness_threshold: int = 14
    order_late_pick_field: LateFromDateType = LateFromDateType.PLACED
    return_or_exchange_config: ReturnOrExchangeConfig = ReturnOrExchangeConfig()
    defective_items_config: DefectiveItemsConfig = DefectiveItemsConfig()
    unworn_or_unopened: bool = False


class EmailConfig(BaseModel):
    send_receipt: bool = True
    is_verified_sender: bool = False


class EmailTemplates(BaseModel):
    generic: str = ""
    cancel_order_request: str = ""
    cancel_order_confirmed: str = ""
    defective_items: str = ""
    missing_items_refund: str = ""
    missing_items_replace: str = ""
    return_exchange: str = ""


class MessageResponseTime(BaseModel):
    class TimeUnit(str, Enum):
        hours = "hours"
        days = "days"
        weeks = "business days"
        months = "working days"

    lower_bound: int = 1
    upper_bound: int = 2
    unit: TimeUnit = TimeUnit.days


class MerchantModel(BaseModel):
    store_url: str
    store_logo_url: str
    contact_us_page_link: str
    email: str
    name: str
    cancellation_policy_config: CancellationPolicyConfig = CancellationPolicyConfig()
    order_config: OrderConfig = OrderConfig()
    email_config: EmailConfig = EmailConfig()
    email_templates: EmailTemplates = EmailTemplates()
    message_response_time: MessageResponseTime = MessageResponseTime()
    pending_payment_order_config: PendingPaymentOrderConfig = PendingPaymentOrderConfig()


class CreateMerchantRequest(MerchantModel):
    pass


class CreateMerchantResponse(BaseModel):
    status: str


class RetrieveMerchantResponse(MerchantModel):
    id: str


class RetrieveMerchantConfigurationResponse(BaseModel):
    store_url: str
    store_logo_url: str
    contact_us_page_link: str
    email: str
    name: str
    cancellation_policy_config: CancellationPolicyConfig = CancellationPolicyConfig()
    order_config: OrderConfig = OrderConfig()
    message_response_time: MessageResponseTime = MessageResponseTime()


class UpdateMerchantRequest(MerchantModel):
    store_url: str = None
    email: str = None
    name: str = None
    cancellation_policy_config: CancellationPolicyConfig = None
    order_config: OrderConfig = None
    email_config: EmailConfig = None
    email_templates: EmailTemplates = None


class UpdateMerchantResponse(BaseModel):
    status: str


# define requests model
class AddMerchantWaitlistRequest(BaseModel):
    email: str
    name: str
    password: str
    other_store_url: Optional[str] = None
    customer_service_email: Optional[str] = None
    reason_to_know_chad: Optional[str] = None
    lateness_threshold: Optional[int] = None
    order_late_pick_field: Optional[str] = None
    auto_cancel_order: Optional[bool] = None


class AddMerchantWaitlistResponse(BaseModel):
    status: str


class UpdateMerchantWaitlistRequest(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    other_store_url: Optional[str] = None
    customer_service_email: Optional[str] = None
    reason_to_know_chad: Optional[str] = None
    lateness_threshold: Optional[int] = None
    order_late_pick_field: Optional[str] = None
    auto_cancel_order: Optional[bool] = None


class UpdateMerchantWaitlistResponse(BaseModel):
    status: str


class ConnectGmailResponse(BaseModel):
    auth_url: str


class ConnectShopifyRequest(BaseModel):
    shop_url: str


class ConnectShopifyResponse(BaseModel):
    auth_url: str


class DisconnectShopifyRequest(BaseModel):
    shop_url: str


class BaseResponse(BaseModel):
    status: str
    message: str
