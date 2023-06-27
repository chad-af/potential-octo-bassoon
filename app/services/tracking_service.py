from typing import Optional

from pydantic import BaseModel

from app.common.logger.log import log_warning
from app.constants import ChadStatus
from app.db.ship24 import Ship24Model, Ship24ModelContext
from app.external.ship24_client import (
    Ship24Client,
    Ship24Recipient,
    Ship24Events,
    Ship24GetTrackerDetailResponse,
)


class TrackingDetails(BaseModel):
    tracker_id: str
    tracking_number: str
    courier: str
    status_code: Optional[str]
    status_category: Optional[str]
    status_milestone: str
    chad_status: str

    estimated_delivery_date: Optional[str]
    delivered_date_time: Optional[str]
    recipient: Optional[Ship24Recipient]
    last_event: Optional[Ship24Events]

    @staticmethod
    def empty():
        return TrackingDetails(
            tracker_id="N/A", tracking_number="N/A", status_milestone="N/A", chad_status="N/A", courier="N/A"
        )

    def is_empty(self):
        return self.tracker_id == "N/A"


class GetTrackingDetailsRequest(BaseModel):
    courier: str
    tracking_number: str


# https://docs.ship24.com/status/#statuscode--statuscategory
SHIP24_STATUS_TO_CHAD_STATUS = {
    "pending": ChadStatus.SHIPPED.value,
    "info_received": ChadStatus.SHIPPED.value,
    "in_transit": ChadStatus.SHIPPED.value,
    "out_for_delivery": ChadStatus.SHIPPED.value,
    "failed_attempt": ChadStatus.DELIVERY_EXCEPTION.value,
    "available_for_pickup": ChadStatus.DELIVERY_EXCEPTION.value,
    "delivered": ChadStatus.DELIVERED.value,
    "exception": ChadStatus.DELIVERY_FAILURE.value,
}


def ship24_to_chad_status(tracking_status: Optional[str]) -> str:
    if not tracking_status or (tracking_status and tracking_status not in SHIP24_STATUS_TO_CHAD_STATUS):
        log_warning(
            "Ship24 returned unrecognized tracking_status.",
            tracking_status=tracking_status,
        )
        return ChadStatus.SHIPPED.value

    return SHIP24_STATUS_TO_CHAD_STATUS[tracking_status]


class TrackingService:
    def __init__(
        self,
        ship24_client: Ship24Client,
    ):
        self.ship24_client = ship24_client

    async def get_tracking_details(self, courier: str, tracking_number: str) -> Optional[TrackingDetails]:
        response = await self._get_tracker_info_from_ship24(
            courier=courier,
            tracking_number=tracking_number,
        )

        if not response or len(response.trackings) == 0:
            log_warning(
                "Ship24 response did not contain any trackings.",
                courier=courier,
                tracking_number=tracking_number,
            )
            return None

        # Note: Its unclear why this api returns this as an array. Just look at the first tracking object.
        tracking = response.trackings[0]
        tracker = tracking.tracker
        timestamps = tracking.statistics.timestamps
        shipment = tracking.shipment
        events = tracking.events

        tracking_details = TrackingDetails(
            **{
                "tracker_id": tracker.trackerId,
                "tracking_number": tracker.trackingNumber,
                "courier": courier,
                "status_code": shipment.statusCode,
                "status_category": shipment.statusCategory,
                "status_milestone": shipment.statusMilestone,
                "chad_status": ship24_to_chad_status(shipment.statusMilestone),
                "estimated_delivery_date": shipment.delivery.estimatedDeliveryDate,
                "delivered_date_time": timestamps.deliveredDatetime,
                "recipient": shipment.recipient,
                "last_event": events[0] if len(events) > 0 else None,
            }
        )

        return tracking_details

    async def _get_tracker_info_from_ship24(
        self, courier: str, tracking_number: str
    ) -> Optional[Ship24GetTrackerDetailResponse]:
        try:
            # Check the cache to halve the number of API calls to Ship24.
            data = Ship24ModelContext.get_by_courier_and_tracking_number(
                courier=courier, tracking_number=tracking_number
            )
            tracker_id = data.ship24_tracker_id if data else None
            if not tracker_id:
                res = await self.ship24_client.initiate_tracker(courier, tracking_number)
                ship24_tracker_id = res.trackings[0].tracker.trackerId
                Ship24Model.insert(
                    courier=courier,
                    tracking_number=tracking_number,
                    ship24_tracker_id=ship24_tracker_id,
                )
                return res

            return await self.ship24_client.get_tracker_results(tracker_id, courier, tracking_number)
        except Exception as e:
            log_warning(
                f"Get tracking details from ship24 failed.",
                exception=e,
                courier=courier,
                tracking_number=tracking_number,
            )
            return None
