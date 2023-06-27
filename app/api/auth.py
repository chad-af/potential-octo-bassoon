from datetime import datetime
from typing import Union

import pytz
from fastapi import APIRouter, Depends, Header, BackgroundTasks, Request

from app.api.utils import send_email, create_activity, create_or_update_user
from app.auth.authentication import (
    get_current_user,
    create_tokens,
    verify_token,
    refresh_token,
    get_store_info,
)
from app.auth.utils import Method
from app.common.exceptions.exceptions import (
    InvalidRequestException,
    OrderDoesNotExistsException,
)
from app.common.monitoring.sentry import ErrorForm
from app.common.utils.order_utils import extract_order_id
from app.dependencies import check_api_key, check_shop_url
from app.external.sendgrid_client import SendgridClient
from app.external.shopify_client import ShopifyClient
import app.db.otp as db_otp
from app.model.activity import ActivityType, UserInfo
from app.model.auth.requests import (
    SendOTPRequestModel,
    EmailOTPVerificationRequestModel,
    VerifyTokenRequestModel,
    RefreshTokenRequestModel,
)
from app.model.auth.responses import (
    BaseResponseModel,
    EmailOTPVerificationResponseModel,
    VerifyTokenResponseModel,
    RefreshTokenResponseModel,
    AuthMeResponseModel,
)
from app.model.merchant import RetrieveMerchantResponse
from app.model.user import User

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(check_api_key), Depends(check_shop_url)],
)


@router.post(
    path="/send-otp",
    description="""
        Check if orders exist with the provided email or order number.
        And if so, send an OTP to the email.
    """,
    response_model=BaseResponseModel,
)
async def send_otp_api(
    requests: SendOTPRequestModel,
    background_tasks: BackgroundTasks,
    request: Request,
    store_info: RetrieveMerchantResponse = Depends(get_store_info),
    sendgrid_client: SendgridClient = Depends(SendgridClient),
    shopify_client: ShopifyClient = Depends(ShopifyClient),
):
    context_name = "Send OTP"
    context_content = {}
    tags = {
        "shop_url": store_info.store_url,
        "email": requests.email,
        "order_number": requests.order_number,
    }
    error_form = ErrorForm(error=InvalidRequestException())
    error_form.context = ErrorForm.ContextForm(
        name=context_name, content=context_content
    )
    error_form.tags = tags
    try:
        if requests.email:
            order = shopify_client.get_order_by_email(
                store_info.store_url, requests.email
            )
        else:
            order = shopify_client.get_order_by_number(
                store_info.store_url, requests.order_number
            )

        edges = order.get("data", {}).get("orders", {}).get("edges", [])
        if len(edges) == 0:
            message = "No orders with the provided data"
            error_form.error = OrderDoesNotExistsException(message)
            raise OrderDoesNotExistsException(message=message, error_form=error_form)

        if requests.email:
            email = requests.email
        else:
            node = edges[0].get("node", {})
            email = node.get("customer", {}).get("email")
            if email is None:
                message = f"Order with the order number [{requests.order_number}] does not have an email"
                error_form.error = OrderDoesNotExistsException(message)
                raise OrderDoesNotExistsException(
                    message=message, error_form=error_form
                )

        otp = db_otp.get_by_email(email)
        store_name = store_info.name
        generic_template = store_info.email_templates.generic
        customer_support_email = store_info.email
        is_verified_sender = store_info.email_config.is_verified_sender
        help_center = store_info.contact_us_page_link
        store_logo_url = store_info.store_logo_url

        subject = f"{store_name} - OTP"

        if otp:
            code = otp.code
            otp.send_count += 1
            otp.updated_at = datetime.now(pytz.timezone("UTC"))
            otp.update()
        else:
            code = db_otp.get_random_otp()
            otp = db_otp.DBOtp.from_dict(
                {
                    "email": email,
                    "code": code,
                }
            )
            otp.save()

        body = f"Your verification code is: <b>{code}</b"

        background_tasks.add_task(
            send_email,
            customer_support_email,
            store_name,
            is_verified_sender,
            store_name,
            customer_support_email,
            email,
            subject,
            body,
            False,
            "OPEN",
            "OTP",
            sendgrid_client,
            generic_template,
            help_center,
            store_logo_url,
        )
        return BaseResponseModel(status="success")
    except OrderDoesNotExistsException as error:
        raise error
    except Exception as error:
        error_form.error = error
        raise InvalidRequestException(error_form=error_form)


@router.post(
    path="/verify-otp",
    description="""
        Verify the email OTP.
        If the otp is valid, return tokens, else return not valid
    """,
    response_model=EmailOTPVerificationResponseModel,
)
async def verify_otp_api(
    requests: EmailOTPVerificationRequestModel,
    request: Request,
    background_tasks: BackgroundTasks,
    shop_url: Union[str, None] = Header(default=None),
    shopify_client: ShopifyClient = Depends(ShopifyClient),
):
    context_name = "Verify OTP"
    context_content = requests.dict()
    tags = {
        "shop_url": shop_url,
        "email": requests.email,
        "order_number": requests.order_number,
    }

    error_form = ErrorForm(error=InvalidRequestException())
    error_form.context = ErrorForm.ContextForm(
        name=context_name, content=context_content
    )
    error_form.tags = tags
    try:
        order_id = None
        if requests.order_number:
            order = shopify_client.get_order_by_number(shop_url, requests.order_number)
            edges = order.get("data", {}).get("orders", {}).get("edges", [])
            if len(edges) == 0:
                message = "No orders with the provided data"
                error_form.error = OrderDoesNotExistsException()
                raise OrderDoesNotExistsException(
                    message=message, error_form=error_form
                )
            node = edges[0].get("node", {})
            email = node.get("customer", {}).get("email")
            if email is None:
                message = f"Order with the order number [{requests.order_number}] does not have an email"
                error_form.error = OrderDoesNotExistsException()
                raise OrderDoesNotExistsException(
                    message=message, error_form=error_form
                )
            order_id = extract_order_id(node.get("id"))
        else:
            email = requests.email

        is_verified = db_otp.verify(email, requests.code)
        if is_verified:
            response = create_tokens(email, shop_url, Method.EMAIL)
            response.order_id = order_id
            user_info = UserInfo(
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                email=email,
            )
            background_tasks.add_task(
                create_activity, ActivityType.LOGIN, shop_url, user_info
            )
            return response

        return EmailOTPVerificationResponseModel(valid=False)
    except OrderDoesNotExistsException as error:
        raise error
    except Exception as error:
        error_form.error = error
        raise InvalidRequestException(error_form=error_form)


@router.post(
    path="/token/verify",
    description="""
       Verify token
    """,
    response_model=VerifyTokenResponseModel,
)
async def verify_token_api(
    request: VerifyTokenRequestModel,
):
    verify_token(request.auth_token)
    return VerifyTokenResponseModel(valid=True)


@router.post(
    path="/token/refresh",
    description="""
       Generate new token based on refresh token
    """,
    response_model=RefreshTokenResponseModel,
)
async def refresh_token_api(
    request: RefreshTokenRequestModel,
):
    response = refresh_token(request.refresh_token)
    return response


@router.get(
    path="/me",
    description="""
        Based on the auth token header, return user information
    """,
    response_model=AuthMeResponseModel,
)
async def auth_me(
    current_user: User = Depends(get_current_user),
    shopify_client: ShopifyClient = Depends(ShopifyClient),
):
    context_name = "Auth Me"
    context_content = {}
    tags = {
        "shop_url": current_user.store_url,
        "email": current_user.email,
    }
    error_form = ErrorForm(error=InvalidRequestException())
    error_form.context = ErrorForm.ContextForm(
        name=context_name, content=context_content
    )
    error_form.tags = tags
    try:
        email = current_user.email
        customer_graph = shopify_client.get_customer_by_email(
            current_user.store_url, email
        )
        customer_node = (
            customer_graph.get("data", {}).get("customers", {}).get("edges", [])
        )

        if len(customer_node) > 0:
            first_name = customer_node[0].get("node", {}).get("firstName", "")
            last_name = customer_node[0].get("node", {}).get("lastName", "")
            shopify_customer_id = customer_node[0].get("node", {}).get("id", "")
        else:
            message = "Customer does not exist with the provided email"
            error_form.error = InvalidRequestException(message)
            raise InvalidRequestException(message=message, error_form=error_form)

        user_id = create_or_update_user(email, shopify_customer_id)

        return AuthMeResponseModel(
            valid=True,
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_id=user_id,
        )
    except InvalidRequestException as error:
        raise error
    except Exception as error:
        error_form.error = error
        raise InvalidRequestException(error_form=error_form)
