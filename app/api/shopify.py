from datetime import datetime, timedelta
from pathlib import Path

import app.db.edit_order as db_edit_order
import validators
from app.service_container import ServiceContainer
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse

from app.api.utils import (
    check_permission,
    get_chad_status,
)
from app.auth.authentication import get_current_user, get_store_info
from app.common.exceptions.exceptions import (
    GetOrderByIdException,
    GetOrdersByEmailException,
    OrderDoesNotExistsException,
    InvalidEmailException,
    ServerException,
)
from app.common.monitoring.sentry import ErrorForm
from app.common.utils.common_functions import float_to_str_with_2_decimals
from app.common.utils.order_utils import (
    extract_order_id,
    shopify_date_str_to_datetime,
    get_amount_from_shopify_price_set,
)
from app.constants import ADMIN_EMAIL, ChadStatus
from app.dependencies import check_api_key, check_shop_url
from app.external.shopify_client import ShopifyClient
from app.model.merchant import RetrieveMerchantResponse, LateFromDateType
from app.model.user import User
from app.services.tracking_service import TrackingService

router = APIRouter(
    prefix="/api/shopify",
    tags=["shopifyOld"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(check_api_key), Depends(check_shop_url)],
)

templates_directory_path = Path(__file__).parent.parent.joinpath("templates")
templates = Jinja2Templates(directory=templates_directory_path)

"""
Retrieves a list of orders from a Shopify store by the associated email.

Args:
    email (str): This is the email of the customer. It is provided as a URL path parameter.
    current_user (User): The currently authenticated user. It defaults to the value returned by the dependency get_current_user.
    shopify_client (ShopifyClient): An instance of ShopifyClient. It defaults to the value returned by the dependency ShopifyClient.

Returns:
    dict: orders and customers which are dictionaries themselves

Raises:
    InvalidEmailException: Raised when the provided email fails validation.
    GetOrdersByEmailException: Raised when there is any exception while fetching the order by email.
        This includes network issues, Shopify API issues, etc.
"""


@router.get("/order/email/{email}")
@inject
async def get_orders_by_email(
    email: str,
    current_user: User = Depends(get_current_user),
    shopify_client: ShopifyClient = Depends(ShopifyClient),
    tracking_service: TrackingService = Depends(Provide[ServiceContainer.tracking_service]),
):
    if not validators.email(email):
        raise InvalidEmailException()
    try:
        # Gets all customers that match the provided email from the given Shopify store
        customers = shopify_client.get_customer_by_email(current_user.store_url, email)

        # Extracts the customer id from the response
        # Note: customer id is globally unique across all Shopify stores
        customer_id = customers.get("data", {}).get("customers", {}).get("edges", [])[0].get("node", {}).get("id")

        # Uses the customer id to fetch the orders from the current user's Shopify store
        result = shopify_client.get_orders_by_customer_id(current_user.store_url, customer_id)

        orders = result.get("data", {}).get("customer", {}).get("orders", {}).get("edges", [])
        for index, order in enumerate(orders):
            line_items = []
            node = order.get("node", {})
            for edge in node.get("lineItems", {}).get("edges", []):
                node_edge = edge.get("node", {})
                current_quantity = node_edge.get("currentQuantity", 0)
                refundable_quantity = node_edge.get("refundableQuantity", 0)
                if current_quantity == refundable_quantity == 0:
                    continue
                line_items.append(edge)

            chad_status, order_details, is_cancelation_failed = get_chad_status(node, extract_order_id(node.get("id")))
            result["data"]["customer"]["orders"]["edges"][index]["node"]["chadFulfillmentStatus"] = chad_status

            result["data"]["customer"]["orders"]["edges"][index]["node"]["lineItems"]["edges"] = line_items

            fulfillments = node.get("fulfillments", [])
            if len(fulfillments) > 0:
                shipped_date = fulfillments[0].get("createdAt")
                delivered_date = fulfillments[0].get("deliveredAt")
                result["data"]["customer"]["orders"]["edges"][index]["node"]["shippedAt"] = shipped_date
                result["data"]["customer"]["orders"]["edges"][index]["node"]["deliveredAt"] = delivered_date

                tracking_info_elem = next(
                    filter(
                        lambda item: item.get("requiresShipping") and item.get("trackingInfo"),
                        fulfillments,
                    ),
                    None,
                )
                if tracking_info_elem:
                    tracking_info = tracking_info_elem.get("trackingInfo")[0]
                    courier = tracking_info.get("company")
                    tracking_number = tracking_info.get("number")
                    if courier and tracking_number:
                        tracking_details = await tracking_service.get_tracking_details(courier, tracking_number)
                        if tracking_details:
                            chad_status = tracking_details.chad_status
                            result["data"]["customer"]["orders"]["edges"][index]["node"][
                                "chadFulfillmentStatus"
                            ] = chad_status
                            result["data"]["customer"]["orders"]["edges"][index]["node"][
                                "trackingDetails"
                            ] = tracking_details.dict()
                        else:
                            result["data"]["customer"]["orders"]["edges"][index]["node"][
                                "trackingInfoErrorMessage"
                            ] = "Status not available"

            if is_cancelation_failed:
                result["data"]["customer"]["orders"]["edges"][index]["node"]["cancelationRequest"] = {
                    "isFailed": True,
                    "reason": "The order is already fulfilled",
                }
            if order_details is not None:
                result["data"]["customer"]["orders"]["edges"][index]["node"] = {
                    **result["data"]["customer"]["orders"]["edges"][index]["node"],
                    **order_details,
                }

        response = {
            "data": {
                "orders": result.get("data", {}).get("customer", {}).get("orders", {}),
                "customers": customers.get("data", {}).get("customers", {}),
            }
        }
        return response
    except Exception as error:
        context_name = "Retrieve Orders By Email"
        context_content = {}
        tags = {
            "shop_url": current_user.store_url,
            "email": current_user.email,
        }
        error_form = ErrorForm(error=error)
        error_form.context = ErrorForm.ContextForm(name=context_name, content=context_content)
        error_form.tags = tags
        raise GetOrdersByEmailException(error_form=error_form)


"""
Retrieves order information by order ID.

Parameters:
    order_id (str): The ID of the order to retrieve.
    current_user (User): The current user object. (Dependency)
    store_info (RetrieveMerchantResponse): Store information. (Dependency)
    shopify_client (ShopifyClient): Shopify API client. (Dependency)

Returns:
    dict: The order information.

Raises:
    OrderDoesNotExistsException: If the order is not found.
    GetOrderByIdException: If an error occurs while retrieving the order.
"""


@router.get("/order/{order_id}")
@inject
async def get_order_by_id(
    order_id: str,
    current_user: User = Depends(get_current_user),
    store_info: RetrieveMerchantResponse = Depends(get_store_info),
    shopify_client: ShopifyClient = Depends(ShopifyClient),  # An instance of the Shopify client
    tracking_service: TrackingService = Depends(Provide[ServiceContainer.tracking_service]),
):
    context_name = "Retrieve Order By Id"
    context_content = {}
    tags = {
        "shop_url": current_user.store_url,
        "email": current_user.email,
        "order_id": order_id,
    }
    error_form = ErrorForm(error=GetOrderByIdException())
    error_form.context = ErrorForm.ContextForm(name=context_name, content=context_content)
    error_form.tags = tags
    is_admin = current_user.email == ADMIN_EMAIL
    try:
        if not is_admin:
            check_permission(shopify_client, current_user, order_id)
        order = shopify_client.get_order_by_id(current_user.store_url, order_id)
        order_details = order.get("data", {}).get("order", {})
        # if the order is not found, order_details will be Null
        if order_details:
            # Fetches the order's chad_status
            # chad_status represents the latest order status as presented to the shopper (end user)
            # Examples include: Ordered, Shipped, Delivered, Refund requested etc.
            fulfillments = order_details.get("fulfillments", [])
            refunds = order_details.get("refunds", [])
            (
                chad_status,
                original_order_details,
                is_cancelation_failed,
            ) = get_chad_status(order_details, order_id)

            if original_order_details is not None:
                order_details = original_order_details

            order_details["chadFulfillmentStatus"] = chad_status

            # If cancelation has failed, provide the reason
            if is_cancelation_failed:
                order_details["cancelationRequest"] = {
                    "isFailed": True,
                    "reason": "The order is already fulfilled",
                }

            # If there is at least on fulfillment in this order, obtain the
            # created and delivered date of the first fulfilment
            # This section of the code will eventually have to be improved to account for
            # the scenario that the first fulfilmment created is not necessarily the first to be delivered
            if len(fulfillments) > 0:
                shipped_date = fulfillments[0].get("createdAt")
                delivered_date = fulfillments[0].get("deliveredAt")
                order_details["shippedAt"] = shipped_date
                order_details["deliveredAt"] = delivered_date

                tracking_info_elem = next(
                    filter(
                        lambda item: item.get("requiresShipping") and item.get("trackingInfo"),
                        fulfillments,
                    ),
                    None,
                )
                if tracking_info_elem:
                    tracking_info = tracking_info_elem.get("trackingInfo")[0]
                    courier = tracking_info.get("company")
                    tracking_number = tracking_info.get("number")
                    if courier and tracking_number:
                        tracking_details = await tracking_service.get_tracking_details(courier, tracking_number)
                        if tracking_details:
                            chad_status = tracking_details.chad_status
                            order_details["chadFulfillmentStatus"] = chad_status
                            order_details["trackingDetails"] = tracking_details.dict()
                        else:
                            order_details["trackingInfoErrorMessage"] = "Status not available"

            # Check that the customer's name matches the shipping address name
            customer_name = order_details.get("customer", {})
            shipping_address_name = order_details.get("shippingAddress", {})

            if customer_name and shipping_address_name:
                order_details["isMatchShopperAndShippingName"] = customer_name == shipping_address_name
            else:
                order_details["isMatchShopperAndShippingName"] = False

            order["data"]["order"] = order_details

            # If an order has been edited to include more expensive items that
            # require a top up payment which has yet to be paid by the shopper
            # Retrieve the original order from the database
            if chad_status == ChadStatus.PAYMENT_PENDING.value or chad_status == ChadStatus.ON_HOLD.value:
                edit_order_obj = db_edit_order.get_by_order_id(order_id)

                if edit_order_obj:
                    order["data"]["order"]["originalOrder"] = {
                        "totalShippingPriceSet": edit_order_obj.totalShippingPriceSet,
                        "currentTotalTaxSet": edit_order_obj.currentTotalTaxSet,
                        "currentTotalPriceSet": edit_order_obj.currentTotalPriceSet,
                        "currentTotalDiscountsSet": edit_order_obj.currentTotalDiscountsSet,
                        "lineItems": edit_order_obj.lineItems,
                    }

            # If an order has been refunded, retrieve the amount refunded + currency
            if chad_status == ChadStatus.REFUNDED.value:
                refund_items = refunds
                refund_amount = 0
                currency_code = ""
                for refund_item in refund_items:
                    refund_amount += get_amount_from_shopify_price_set(refund_item, "totalRefundedSet")
                    currency_code = refund_item.get("totalRefundedSet", {}).get("shopMoney", {}).get("currencyCode")
                if refund_items:
                    order["data"]["order"]["refundedPriceSet"] = {
                        "shopMoney": {
                            "amount": float_to_str_with_2_decimals(refund_amount),
                            "currencyCode": currency_code,
                        }
                    }

            # Sets the threshold for determining when an order is considered late
            order["data"]["order"]["isLate"] = False
            order["data"]["order"]["lateThreshold"] = None

            lateness_threshold = store_info.order_config.lateness_threshold or 14
            order_late_pick_field = store_info.order_config.order_late_pick_field or LateFromDateType.PLACED

            # Determines whether an order is late based on the lateness_threshold
            if order_late_pick_field == LateFromDateType.PLACED:
                order_date_str = order_details.get("createdAt", "")
                order_date = shopify_date_str_to_datetime(order_date_str)
                if datetime.now() - order_date > timedelta(days=lateness_threshold):
                    order["data"]["order"]["isLate"] = True
                late_threshold = order_date + timedelta(days=lateness_threshold)
                order["data"]["order"]["lateThreshold"] = late_threshold.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:  # shipped
                if chad_status != ChadStatus.SHIPPED.value:
                    return order

                if len(fulfillments) > 0:
                    shipped_date_str = fulfillments[0].get("updatedAt")
                    shipped_date = shopify_date_str_to_datetime(shipped_date_str)
                else:
                    shipped_date_str = order_details.get("updatedAt")
                    shipped_date = shopify_date_str_to_datetime(shipped_date_str)

                if datetime.now() - shipped_date > timedelta(days=lateness_threshold):
                    order["data"]["order"]["isLate"] = True
                late_threshold = shipped_date + timedelta(days=lateness_threshold)
                order["data"]["order"]["lateThreshold"] = late_threshold.strftime("%Y-%m-%dT%H:%M:%SZ")
            return JSONResponse(content=order)  # TODO: Change this to OrderResponseModel eventually.
        else:
            raise OrderDoesNotExistsException(error_form=error_form)
    except Exception as error:
        if isinstance(error, ServerException):
            raise error
        error_form.error = error
        raise GetOrderByIdException(error_form=error_form)
