import logging
from typing import Optional, Dict

from fastapi import HTTPException

from app.common.monitoring.sentry import ErrorForm


class ErrorCodes:
    SERVER_ERROR = 0
    INVALID_REQUEST_ERROR = 100000
    TOKEN_EXPIRED = 100001
    WRONG_TOKEN = 100002
    INVALID_STORE_URL = 100003
    FORBIDDEN_ID = 100004
    DATA_VALIDATION_ERROR = 110001
    INVALID_EMAIL = 110002
    GET_ORDER_BY_ID_ERROR = 120001
    GET_ORDERS_BY_EMAIL_ERROR = 120002
    ORDER_DOES_NOT_EXISTS_ERROR = 120003
    CHANGE_SHIPPING_ADDRESS_ERROR = 130001


class ServerException(HTTPException):
    def __init__(
        self,
        internal_status_code: int,
        message: str,
        http_status_code: int,
        error_form: ErrorForm = None,
        data: Optional[Dict] = None,
        log_level: int = logging.ERROR,
    ):
        HTTPException.__init__(self, http_status_code)
        self.internal_status_code = internal_status_code
        self.message = message
        self.error_form = error_form
        self.data = data
        self.log_level = log_level
        self.args = (message,)

    def to_dict(self):
        return {
            **(self.data or {}),
            "internal_status_code": self.internal_status_code,
            "message": self.message,
        }

    def __str__(self):
        return self.message or str(self.to_dict())


class ApiException(HTTPException):
    def __init__(
        self,
        message: str,
        http_status_code: int,
        data: Optional[Dict] = None,
        log_level: int = logging.ERROR,
    ):
        HTTPException.__init__(self, http_status_code)
        self.message = message
        self.data = data
        self.log_level = log_level
        self.args = (message,)

    def to_dict(self):
        return {
            **(self.data or {}),
            "message": self.message,
        }

    def __str__(self):
        return self.message or str(self.to_dict())


class ClientException(ApiException):
    def __init__(self, message=None, status_code: int = 400):
        super().__init__(
            message=message,
            http_status_code=status_code,
            log_level=logging.INFO,
        )


class InternalServerError(ServerException):
    def __init__(self, message=None, error_form: ErrorForm = None):
        super().__init__(
            internal_status_code=ErrorCodes.SERVER_ERROR,
            message=message,
            http_status_code=500,
            log_level=logging.ERROR,
            error_form=error_form,
        )


class InvalidRequestException(ServerException):
    """Invalid error."""

    def __init__(self, message=None, error_form: ErrorForm = None):
        super().__init__(
            internal_status_code=ErrorCodes.INVALID_REQUEST_ERROR,
            message=message or "Invalid Request",
            http_status_code=400,
            log_level=logging.ERROR,
            error_form=error_form,
        )


class ValidationError(ServerException):
    """Validation error."""

    def __init__(self, message=None):
        super().__init__(
            internal_status_code=ErrorCodes.DATA_VALIDATION_ERROR,
            message=message or "Invalid Request",
            http_status_code=403,
        )


class TokenExpiredException(ServerException):
    def __init__(self, message=None):
        super().__init__(
            internal_status_code=ErrorCodes.TOKEN_EXPIRED,
            message=message or "Token Expired",
            http_status_code=401,
            log_level=logging.WARNING,
        )


class WrongTokenException(ServerException):
    def __init__(self, message: Optional[str] = None):
        super().__init__(
            internal_status_code=ErrorCodes.WRONG_TOKEN,
            message=message or "Wrong Token",
            http_status_code=401,
            log_level=logging.ERROR,
        )


class InvalidStoreUrlException(ServerException):
    def __init__(self, message: Optional[str] = None):
        super().__init__(
            internal_status_code=ErrorCodes.INVALID_STORE_URL,
            message=message or "Invalid Store url",
            http_status_code=401,
            log_level=logging.ERROR,
        )


class GetOrderByIdException(ServerException):
    def __init__(self, message: Optional[str] = None, error_form: ErrorForm = None):
        super().__init__(
            internal_status_code=ErrorCodes.GET_ORDER_BY_ID_ERROR,
            message=message or "Invalid Order id",
            http_status_code=400,
            log_level=logging.ERROR,
            error_form=error_form,
        )


class GetOrdersByEmailException(ServerException):
    def __init__(self, message: Optional[str] = None, error_form: ErrorForm = None):
        super().__init__(
            internal_status_code=ErrorCodes.GET_ORDERS_BY_EMAIL_ERROR,
            message=message or "Invalid Email",
            http_status_code=400,
            log_level=logging.ERROR,
            error_form=error_form,
        )


class ChangeShippingAddressException(ServerException):
    def __init__(self, message: Optional[str] = None, error_form: ErrorForm = None):
        super().__init__(
            internal_status_code=ErrorCodes.CHANGE_SHIPPING_ADDRESS_ERROR,
            message=message or "Failed to change shipping address",
            http_status_code=400,
            log_level=logging.ERROR,
            error_form=error_form,
        )


class OrderDoesNotExistsException(ServerException):
    def __init__(self, message: Optional[str] = None, error_form: ErrorForm = None):
        super().__init__(
            internal_status_code=ErrorCodes.ORDER_DOES_NOT_EXISTS_ERROR,
            message=message or "Order does not exists",
            http_status_code=404,
            log_level=logging.WARNING,
            error_form=error_form,
        )


class InvalidEmailException(ServerException):
    def __init__(self, message: Optional[str] = None, error_form: ErrorForm = None):
        super().__init__(
            internal_status_code=ErrorCodes.INVALID_EMAIL,
            message=message or "Invalid Email",
            http_status_code=400,
            log_level=logging.ERROR,
            error_form=error_form,
        )


class PermissionDenied(ServerException):
    def __init__(self, message: Optional[str] = None, error_form: ErrorForm = None):
        super().__init__(
            internal_status_code=ErrorCodes.FORBIDDEN_ID,
            message=message or "Action not allowed for current user.",
            http_status_code=403,
            log_level=logging.ERROR,
            error_form=error_form,
        )
