from typing import Optional

import validators
from pydantic import BaseModel, root_validator

from app.common.utils.validators import must_be_only_one_of


class SendOTPRequestModel(BaseModel):
    email: Optional[str]
    order_number: Optional[str]

    @root_validator(pre=True)
    def validate_email_or_order_number(cls, values):
        email, order_number = values.get("email"), values.get("order_number")
        must_be_only_one_of(email=email, order_number=order_number)
        if email and not validators.email(email):
            raise ValueError(f"{email} is invalid Email")
        return values


class EmailOTPVerificationRequestModel(BaseModel):
    email: Optional[str]
    order_number: Optional[str]
    code: str

    @root_validator(pre=True)
    def validate_email_or_order_number(cls, values):
        email, order_number = values.get("email"), values.get("order_number")
        must_be_only_one_of(email=email, order_number=order_number)
        if email and not validators.email(email):
            raise ValueError(f"{email} is invalid Email")
        return values


class VerifyTokenRequestModel(BaseModel):
    auth_token: str


class RefreshTokenRequestModel(BaseModel):
    refresh_token: str
