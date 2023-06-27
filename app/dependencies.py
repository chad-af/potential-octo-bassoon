from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from app.constants import ADMIN_API_KEY, API_KEY

API_KEY_HEADER = APIKeyHeader(name="API_KEY", auto_error=False)
SHOP_URL_HEADER = APIKeyHeader(name="shop-url", auto_error=False)


async def check_api_key(
    api_key_header: str = Security(API_KEY_HEADER),
):
    if api_key_header == API_KEY:
        return api_key_header
    elif api_key_header == ADMIN_API_KEY:  # admin
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


async def check_shop_url(
    shop_url_header: str = Security(SHOP_URL_HEADER),
) -> str:
    if shop_url_header is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Shop url is missing in the header"
        )
    return shop_url_header


async def check_admin_api_key(
    api_key_header: str = Security(API_KEY_HEADER),
):
    if api_key_header == ADMIN_API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate admin credentials",
        )
