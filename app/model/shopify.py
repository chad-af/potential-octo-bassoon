import base64
from typing import Optional

from pydantic import BaseModel


class BaseResponse(BaseModel):
    status: str
    message: str


class ChangeShippingAddressRequests(BaseModel):
    input_1: str  # first_name
    input_2: str  # last_name
    add_1: str  # address1
    add_2: str  # address2
    ci: str  # city
    pro: str  # province
    co: str  # country
    pc: str  # zip

    def decode(self):
        for k, v in self.__dict__.items():
            self.__dict__[k] = self._decode(v)

    @staticmethod
    def _decode(encoded_str: str) -> str:
        return base64.b64decode(encoded_str).decode("utf-8")


class RefundOrderRequests(BaseModel):
    message: str


class ProductsInfoRequestModel(BaseModel):
    product_ids: list[str]


class EditOrderItemInfoModel(BaseModel):
    id: str
    variantId: str
    count: int
    image: Optional[str]
    name: str
    pricePerItem: dict


class EditOrderGetInfoRequests(BaseModel):
    sender: str
    order_id: str
    items_info: list[EditOrderItemInfoModel]


class SubmitEditOrderRequests(BaseModel):
    calculatedOrderId: str
    orderId: str
