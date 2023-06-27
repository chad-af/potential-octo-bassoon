from fastapi import HTTPException


class TokenException(HTTPException):
    pass


class NoAuthorizationError(TokenException):
    """
    An error raised when no authorization token was found in a protected endpoint
    """

    pass


class JWTExtendedException(TokenException):
    """
    Base except which all flask_jwt_extended errors extend
    """

    pass


class JWTDecodeError(JWTExtendedException):
    """
    An error decoding a JWT
    """

    pass