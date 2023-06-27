from asyncio import Task

from typing import Coroutine

from fireo.fields import TextField, IDField, DateTime, MapField
import asyncio
from fireo.models import Model


class DBOrder(Model):
    id = IDField()
    order_id = TextField()
    status = TextField()
    created_at = DateTime(auto=True)
    updated_at = DateTime(auto=True)
    original_order_details = MapField()

    class Meta:
        collection_name = "order"


class OrderModelContext:
    @staticmethod
    async def get_order_by_id(order_id: str) -> DBOrder:
        return await asyncio.to_thread(OrderModelContext._get_order_by_id, order_id)

    @staticmethod
    def _get_order_by_id(order_id: str) -> DBOrder:
        return DBOrder.collection.filter("order_id", "==", order_id).get()


def get_by_order_id(order_id: str) -> DBOrder:
    order = DBOrder.collection.filter("order_id", "==", order_id).get()
    return order


def delete_order(order: DBOrder):
    DBOrder.collection.delete(order.key)
