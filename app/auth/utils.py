import uuid
from calendar import timegm

import jwt

from datetime import datetime, timedelta
from enum import IntEnum

from app.auth.exceptions import JWTDecodeError

IDENTITY_CLAIM_KEY = "identity"
USER_CLAIMS_KEY = "userClaims"


class Method(IntEnum):
    EMAIL = 0
    ORDER_NUMBER = 1


def build_user_claims(
    store_url: str,
    method: Method,
):
    return {
        "storeUrl": store_url,
        "method": method,
    }


def _create_csrf_token():
    return str(uuid.uuid4())


def _encode_jwt(
    additional_token_data, expires_delta, secret, algorithm, json_encoder=None
):
    uid = _create_csrf_token()
    now = datetime.utcnow()
    token_data = {"iat": now, "nbf": now, "jti": uid}
    # If expires_delta is False, the JWT should never expire
    # and the 'exp' claim is not set.
    if expires_delta:
        token_data["exp"] = now + expires_delta
    token_data.update(additional_token_data)
    encoded_token = jwt.encode(token_data, secret, algorithm, json_encoder=json_encoder)
    return encoded_token


def encode_access_token(
    identity,
    secret,
    algorithm,
    expires_delta,
    fresh,
    user_claims,
    identity_claim_key=IDENTITY_CLAIM_KEY,
    user_claims_key=USER_CLAIMS_KEY,
    audience=None,
    json_encoder=None,
):
    """
    Creates a new encoded (utf-8) access token.

    :param json_encoder:
    :param identity: Identifier for who this token is for (ex, username). This
                     data must be json serializable
    :param secret: Secret key to encode the JWT with
    :param algorithm: Which algorithm to encode this JWT with
    :param expires_delta: How far in the future this token should expire
                          (set to False to disable expiration)
    :type expires_delta: datetime.timedelta or False
    :param fresh: If this should be a 'fresh' token or not. If a
                  datetime.timedelta is given this will indicate how long this
                  token will remain fresh.
    :param user_claims: Custom claims to include in this token. This data must
                        be json serializable
    :param identity_claim_key: Which key should be used to store the identity
    :param user_claims_key: Which key should be used to store the user claims
    :return: Encoded access token
    """
    if isinstance(fresh, timedelta):
        now = datetime.utcnow()
        fresh = timegm((now + fresh).utctimetuple())
    token_data = {
        identity_claim_key: identity,
        "fresh": fresh,
        "type": "access",
        "aud": audience,
    }
    # Don't add extra data to the token if user_claims is empty.
    if user_claims:
        token_data[user_claims_key] = user_claims
    return _encode_jwt(
        token_data, expires_delta, secret, algorithm, json_encoder=json_encoder
    )


def encode_refresh_token(
    identity,
    secret,
    algorithm,
    expires_delta,
    user_claims,
    identity_claim_key=IDENTITY_CLAIM_KEY,
    user_claims_key=USER_CLAIMS_KEY,
    audience=None,
    json_encoder=None,
):
    """
    Creates a new encoded (utf-8) refresh token.

    :param audience:
    :param json_encoder:
    :param identity: Some identifier used to identify the owner of this token
    :param secret: Secret key to encode the JWT with
    :param algorithm: Which algorithm to use for the toek
    :param expires_delta: How far in the future this token should expire
                          (set to False to disable expiration)
    :type expires_delta: datetime.timedelta or False
    :param user_claims: Custom claims to include in this token. This data must
                        be json serializable
    :param identity_claim_key: Which key should be used to store the identity
    :param user_claims_key: Which key should be used to store the user claims
    :return: Encoded refresh token
    """
    token_data = {identity_claim_key: identity, "type": "refresh", "aud": audience}
    # Don't add extra data to the token if user_claims is empty.
    if user_claims:
        token_data[user_claims_key] = user_claims
    return _encode_jwt(
        token_data, expires_delta, secret, algorithm, json_encoder=json_encoder
    )


def decode_jwt(
    encoded_token,
    secret,
    algorithm,
    identity_claim_key=IDENTITY_CLAIM_KEY,
    user_claims_key=USER_CLAIMS_KEY,
    audience=None,
    leeway=0,
    allow_expired=False,
):
    """
    Decodes an encoded JWT

    :param encoded_token: The encoded JWT string to decode
    :param secret: Secret key used to encode the JWT
    :param algorithm: Algorithm used to encode the JWT
    :param identity_claim_key: expected key that contains the identity
    :param user_claims_key: expected key that contains the user claims
    :param audience: expected audience in the JWT
    :param leeway: optional leeway to add some margin around expiration times
    :param allow_expired: Options to ignore exp claim validation in token
    :return: Dictionary containing contents of the JWT
    """
    options = {}
    if allow_expired:
        options["verify_exp"] = False
    # This call verifies the ext, iat, nbf, and aud claims
    data = jwt.decode(
        encoded_token,
        secret,
        algorithms=[algorithm],
        audience=audience,
        leeway=leeway,
        options=options,
    )
    # Make sure that any custom claims we expect in the token are present
    if "jti" not in data:
        data["jti"] = None
    if identity_claim_key not in data:
        raise JWTDecodeError(500, "Missing claim: {}".format(identity_claim_key))

    if "type" not in data:
        data["type"] = "access"
    if data["type"] not in ("refresh", "access", "confirmation", "invitation"):
        raise JWTDecodeError(500, "Missing or invalid claim: type")

    if data["type"] == "access":
        if "fresh" not in data:
            data["fresh"] = False
    if user_claims_key not in data:
        data[user_claims_key] = {}
    return data
