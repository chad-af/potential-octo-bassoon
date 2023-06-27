from typing import Union

from fireo.models import Model
from fireo.fields import TextField, IDField, MapField

from app.model.merchant import CreateMerchantRequest, RetrieveMerchantResponse


COLLECTION_NAME = "merchant"


class DBMerchant(Model):
    id = IDField()
    store_url = TextField()
    store_logo_url = TextField()
    contact_us_page_link = TextField()
    email = TextField()
    name = TextField()
    cancellation_policy_config = MapField()
    """
    {
    "auto_cancel_order": true
    "time_limit_after_placing_order": 10 # hours
    }
    """
    order_config = MapField()
    """
    {
    "lateness_threshold": 10,   # days
    "order_late_pick_field": "placed" or "shipped
    }
    """
    email_config = MapField()
    """
    {
    "send_receipt": true,
    "is_verified_sender": false
    }
    """
    email_templates = MapField()
    """
    {
    "generic": "<html></html>",
    "cancel_order_request": "<html></html>",
    "cancel_order_confirmed": "<html></html>",
    "defective_items": "<html></html>",
    "missing_items_refund": "<html></html>",
    "missing_items_replace": "<html></html>",
    }
    """
    message_response_time = MapField()
    """
    {
    "lower_bound": 1,
    "upper_bound": 2,
    "unit": "hours",
    }
    """

    pending_payment_order_config = MapField()
    """
    {
    "auto_cancel_order": true
    "time_limit_after_pending_payment": 3 # days
    }
    """

    class Meta:
        collection_name = COLLECTION_NAME


def create(req_obj: CreateMerchantRequest):
    merchant = DBMerchant.from_dict(req_obj.dict())
    merchant.save()


def retrieve_by_store_url(
    store_url: str, return_db_object: bool = False
) -> Union[RetrieveMerchantResponse, DBMerchant, None]:
    merchant_db_obj = DBMerchant.collection.filter("store_url", "==", store_url).get()
    if merchant_db_obj is None:
        return None
    if return_db_object:
        return merchant_db_obj

    return RetrieveMerchantResponse(**merchant_db_obj.to_dict())
