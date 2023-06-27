from datetime import timedelta, datetime
from aenum import MultiValue, Enum
from typing import Optional, Union

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidSignatureError, DecodeError

from app.auth.exceptions import NoAuthorizationError
from app.auth.utils import (
    encode_refresh_token,
    USER_CLAIMS_KEY,
    decode_jwt,
    build_user_claims,
    Method,
    encode_access_token,
    IDENTITY_CLAIM_KEY,
)
from app.common.exceptions.exceptions import (
    TokenExpiredException,
    WrongTokenException,
    InvalidStoreUrlException,
)
from app.constants import ADMIN_EMAIL, ADMIN_API_KEY
from app.dependencies import check_api_key
from app.environment import env
from app.model.auth.responses import (
    RefreshTokenResponseModel,
    EmailOTPVerificationResponseModel,
)
from app.model.user import User
import app.db.merchant as db_merchant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenType(Enum):
    _init_ = "value string_value"
    _settings_ = MultiValue

    ACCESS = 0, "access"
    REFRESH = 1, "refresh"

    def __int__(self):
        return self.value


def get_current_user(
    token: str = Depends(oauth2_scheme),
    api_key: str = Depends(check_api_key),
    shop_url: Union[str, None] = Header(default=None),
):
    if api_key == ADMIN_API_KEY:
        return User(email=ADMIN_EMAIL, store_url=shop_url)
    decoded_token = verify_token(token)
    store_url = decoded_token[USER_CLAIMS_KEY].get("storeUrl")
    if shop_url != store_url:
        raise InvalidStoreUrlException("Store url does not match in the token")
    user = User(email=decoded_token["identity"], store_url=store_url)
    return user


def get_store_info(
    shop_url: Union[str, None] = Header(default=None),
):
    store_info = db_merchant.retrieve_by_store_url(shop_url)
    if not store_info:
        raise InvalidStoreUrlException(f"Store url [{shop_url}] does not exist")
    return store_info


def create_refresh_token(
    identity: str, user_claims: dict, expires_delta: Optional[timedelta] = None
):
    return encode_refresh_token(
        identity,
        env.JWT_SECRET_KEY,
        env.JWT_ALGORITHM,
        expires_delta,
        user_claims,
        audience=env.JWT_AUDIENCE,
    )


def prepare_refresh_token(email: str, user_claims: dict):
    expires_delta = None

    if env.JWT_REFRESH_TOKEN_EXPIRE_MINUTES:
        expires_delta = timedelta(minutes=env.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)

    return create_refresh_token(
        identity=email, user_claims=user_claims, expires_delta=expires_delta
    )


def prepare_auth_token_claims(refresh_token: str):
    decoded_ref_token = verify_token(refresh_token, request_type="refresh")
    claims = decoded_ref_token[USER_CLAIMS_KEY]
    return claims


def verify_token(
    token: str,
    request_type: str = TokenType.ACCESS.string_value,
    verify_user_claims=True,
):
    errors = []
    decoded_token = None
    try:
        decoded_token = decode_jwt(
            token,
            env.JWT_SECRET_KEY,
            env.JWT_ALGORITHM,
            audience=env.JWT_AUDIENCE,
        )
    except ExpiredSignatureError:
        raise TokenExpiredException

    except NoAuthorizationError as e:
        errors.append(str(e))

    except (InvalidSignatureError, DecodeError):
        raise WrongTokenException

    if not decoded_token:
        raise NoAuthorizationError(errors[0])

    verify_token_type(decoded_token, expected_type=request_type)

    return decoded_token


def verify_token_type(decoded_token: dict, expected_type: str):
    if decoded_token["type"] != expected_type:
        raise WrongTokenException("Only {} tokens are allowed".format(expected_type))


def create_tokens(
    email: str, store_url: str, method: Method
) -> EmailOTPVerificationResponseModel:
    user_claims = build_user_claims(store_url, method)
    refresh_token = prepare_refresh_token(email, user_claims)
    auth_token_claims = prepare_auth_token_claims(refresh_token)
    auth_token = prepare_auth_token(email, auth_token_claims)

    ref_expires_in = get_token_expires_in(refresh_token, "refresh")
    auth_token_expires_in = get_token_expires_in(auth_token, "access")
    return EmailOTPVerificationResponseModel(
        valid=True,
        auth_token=auth_token,
        refresh_token=refresh_token,
        expires_in=auth_token_expires_in,
        refresh_token_expires_in=ref_expires_in,
    )


def prepare_auth_token(email: str, user_claims: dict):
    expires_delta = timedelta(minutes=env.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    auth_token = create_access_token(
        identity=email, user_claims=user_claims, expires_delta=expires_delta
    )
    return auth_token


def create_access_token(
    identity: str,
    user_claims: dict = None,
    expires_delta=timedelta(days=1),
) -> str:
    return encode_access_token(
        identity,
        env.JWT_SECRET_KEY,
        env.JWT_ALGORITHM,
        expires_delta,
        False,
        user_claims,
        audience=env.JWT_AUDIENCE,
    )


def get_token_expires_in(token: str, token_type: str) -> float:
    decoded_ref_token = verify_token(token, request_type=token_type)
    expires_in = None
    if "exp" in decoded_ref_token:
        expires_at = datetime.utcfromtimestamp(decoded_ref_token["exp"])
        expires_in = (expires_at - datetime.utcnow()).total_seconds()
    return expires_in


def refresh_token(ref_token: str) -> RefreshTokenResponseModel:
    ref_token_expires_in = get_token_expires_in(ref_token, "refresh")
    decoded_ref_token = verify_token(ref_token, "refresh")

    expires_delta = timedelta(minutes=env.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    user_claims = {
        **decoded_ref_token[USER_CLAIMS_KEY],
    }

    email = decoded_ref_token[IDENTITY_CLAIM_KEY]

    auth_token = create_access_token(
        identity=email, user_claims=user_claims, expires_delta=expires_delta
    )
    return RefreshTokenResponseModel(
        auth_token=auth_token,
        expires_in=expires_delta.total_seconds(),
        refresh_token=ref_token,
        refresh_token_expires_in=ref_token_expires_in,
    )
