import logging
import uuid
from datetime import datetime
from typing import Union

import pytz

import app.db.order as db_order
import app.db.user as db_user
from app.common.exceptions.exceptions import PermissionDenied
from app.common.monitoring.sentry import report_exception
from app.common.utils.order_utils import get_amount_from_shopify_price_set
from app.constants import ChadStatus
from app.external.shopify_client import ShopifyClient
from app.model.user import User

logger = logging.getLogger(__name__)


def check_permission(shopify_client: ShopifyClient, user: User, order_id: str):
    response = shopify_client.get_customer_by_order_id(user.store_url, order_id)
    if response.data.order.customer.email != user.email:
        raise PermissionDenied()


def get_chad_status(
    order_details: dict, order_id: str
) -> (str, Union[dict, None], bool):
    chad_status = ChadStatus.ORDERED.value

    is_cancelation_failed = False
    try:
        current_total_price = get_amount_from_shopify_price_set(
            order_details, "currentTotalPriceSet"
        )
        financial_status = order_details.get("displayFinancialStatus")
        fulfillments = order_details.get("fulfillments", [])
        if len(fulfillments) > 0:
            shipped_date = fulfillments[0].get("createdAt")
            delivered_date = fulfillments[0].get("deliveredAt")
            order_details["shippedAt"] = shipped_date
            order_details["deliveredAt"] = delivered_date

        fulfillments_statuses = [
            fulfillment.get("displayStatus", "") for fulfillment in fulfillments
        ]
        try:
            order_obj = db_order.get_by_order_id(order_id)
            chad_status = order_obj.status

            if chad_status == "CANCELATION_FAILED":
                is_cancelation_failed = True
                chad_status = None
            else:
                return (
                    chad_status,
                    order_obj.original_order_details,
                    is_cancelation_failed,
                )
        except:
            chad_status = None

        if chad_status is None:
            if (
                "IN_TRANSIT" in fulfillments_statuses
                or "FULFILLED" in fulfillments_statuses
            ):
                chad_status = ChadStatus.SHIPPED.value
            else:
                set_statuses = set(fulfillments_statuses)
                if len(set_statuses) == 1 or len(set_statuses) == 2:
                    if len(set_statuses) == 1 and "CANCELED" in set_statuses:
                        chad_status = ChadStatus.REFUNDED.value
                    if len(set_statuses) == 1 and "DELIVERED" in set_statuses:
                        chad_status = ChadStatus.DELIVERED.value
                    if (
                        len(set_statuses) == 2
                        and "CANCELED" in set_statuses
                        and "DELIVERED" in set_statuses
                    ):
                        chad_status = ChadStatus.DELIVERED.value

            if chad_status is None:
                fulfillment_status = order_details.get("displayFulfillmentStatus", "")
                refund_items = order_details.get("refunds", [])
                fulfillment_status_map = {
                    "FULFILLED": ChadStatus.SHIPPED.value,
                    "PARTIALLY_FULFILLED": ChadStatus.SHIPPED.value,
                    "IN_PROGRESS": ChadStatus.SHIPPED.value,
                    "OPEN": ChadStatus.ORDERED.value,
                    "PENDING_FULFILLMENT": ChadStatus.ORDERED.value,
                    "SCHEDULED": ChadStatus.ORDERED.value,
                    "UNFULFILLED": ChadStatus.ORDERED.value,
                    "ON_HOLD": ChadStatus.ON_HOLD.value,
                }
                if fulfillment_status == "UNFULFILLED" and len(refund_items) > 0:
                    if current_total_price == 0:
                        chad_status = ChadStatus.REFUNDED.value
                    else:
                        total_outstanding_price = get_amount_from_shopify_price_set(
                            order_details, "totalOutstandingSet"
                        )
                        if (
                            financial_status == "PARTIALLY_PAID"
                            or total_outstanding_price > 0
                        ):
                            chad_status = ChadStatus.PAYMENT_PENDING.value

                if chad_status is None:
                    chad_status = fulfillment_status_map.get(
                        fulfillment_status, ChadStatus.ORDERED.value
                    )
    except Exception as e:
        print(str(e))

    return chad_status, None, is_cancelation_failed


def create_or_update_user(email: str, shopify_customer_id: str) -> str:
    try:
        user = db_user.get_by_email(email)
        if user is None:
            user_id = str(uuid.uuid4())
            user = db_user.DBUser.from_dict(
                {
                    "user_id": user_id,
                    "shopify_customer_id": shopify_customer_id,
                    "email": email,
                }
            )
            user.save()
        else:
            user.last_login_at = datetime.now(pytz.timezone("UTC"))
            user.update()

        return user.user_id
    except Exception as e:
        context_name = "Create Or Update User"
        context_content = {}
        tags = dict(
            activity_type=email,
            shopify_customer_id=shopify_customer_id,
        )
        report_exception(
            e,
            context_name=context_name,
            context_content=context_content,
            tags=tags,
        )
