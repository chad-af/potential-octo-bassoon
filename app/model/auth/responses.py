from typing import Optional

from pydantic import BaseModel


class BaseResponseModel(BaseModel):
    status: str
    message: Optional[str]


class RefreshTokenResponseModel(BaseModel):
    auth_token: Optional[str]
    refresh_token: Optional[str]
    expires_in: Optional[float]
    refresh_token_expires_in: Optional[float]


class EmailOTPVerificationResponseModel(RefreshTokenResponseModel):
    order_id: Optional[str]
    valid: bool


class VerifyTokenResponseModel(BaseModel):
    valid: bool


class AuthMeResponseModel(BaseModel):
    valid: bool
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    user_id: Optional[str]
