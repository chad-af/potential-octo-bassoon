from pydantic import BaseModel
from typing import Optional, List

from app.common.exceptions.exceptions import ServerException
from app.common.logger.log import log_warning
from app.external.base_client import BaseClient
from app.external.geocode_client import GeoCoordinates

SHIP_24_API_BASE_URL = "https://api.ship24.com/public/v1/trackers"


class Ship24Exception(ServerException):
    def __init__(self, message: str, **kwargs):
        super().__init__(0, message, 500, data=kwargs)


class _Ship24TrackerInfo(BaseModel):
    trackerId: str
    trackingNumber: Optional[str]
    isSubscribed: Optional[bool]
    shipmentReference: Optional[str]
    createdAt: Optional[str]


class _Ship24Delivery(BaseModel):
    estimatedDeliveryDate: Optional[str]
    service: Optional[str]
    signedBy: Optional[str]


class _Ship24TrackingNumber(BaseModel):
    tn: Optional[str]


class Ship24Recipient(BaseModel):
    name: Optional[str]
    address: Optional[str]
    postCode: Optional[str]
    city: Optional[str]
    subdivision: Optional[str]


class Ship24ShipmentInfo(BaseModel):
    shipmentId: str
    statusCode: Optional[str]
    statusCategory: Optional[str]
    statusMilestone: Optional[str]
    originCountryCode: Optional[str]
    destinationCountryCode: Optional[str]
    delivery: _Ship24Delivery
    trackingNumbers: List[_Ship24TrackingNumber]
    recipient: Ship24Recipient


class Ship24Events(BaseModel):
    eventId: str
    trackingNumber: str
    eventTrackingNumber: str
    status: str
    occurrenceDatetime: str
    datetime: str
    location: Optional[str]
    statusCode: Optional[str]
    statusCategory: Optional[str]
    statusMilestone: Optional[str]
    geoCoordinates: Optional[GeoCoordinates]


class _Timestamps(BaseModel):
    infoReceivedDatetime: Optional[str]
    inTransitDatetime: Optional[str]
    outForDeliveryDatetime: Optional[str]
    failedAttemptDatetime: Optional[str]
    availableForPickupDatetime: Optional[str]
    exceptionDatetime: Optional[str]
    deliveredDatetime: Optional[str]


class Ship24TrackerStats(BaseModel):
    timestamps: _Timestamps


class Ship24TrackerDetails(BaseModel):
    tracker: _Ship24TrackerInfo
    shipment: Ship24ShipmentInfo
    events: List[Ship24Events]
    statistics: Ship24TrackerStats


class Ship24GetTrackerDetailResponse(BaseModel):
    trackings: List[Ship24TrackerDetails]


class Ship24Client(BaseClient):
    # more information about the api docs
    # https://docs.ship24.com/tracking-api-reference/#/
    def __init__(self, ship24_api_key: str):
        super().__init__()
        self.authorization = f"Bearer {ship24_api_key}"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.authorization,
        }

    async def initiate_tracker(self, courier: str, tracking_number: str) -> Optional[Ship24GetTrackerDetailResponse]:
        # https://docs.ship24.com/tracking-api-reference/#/operations/create-tracker-and-get-tracking-results
        url = f"{SHIP_24_API_BASE_URL}/track"
        async with self.session.post(url, headers=self.headers, json={"trackingNumber": tracking_number}) as response:
            if response.status in [200, 201]:
                response_json = await response.json()
                return Ship24GetTrackerDetailResponse(**response_json["data"])
            else:
                # log_warning(
                #     "Could not initiate Ship24 tracker.",
                #     courier=courier,
                #     tracking_number=tracking_number,
                # )
                return None

    async def get_tracker_results(
        self, tracker_id: str, courier: str, tracking_number: str
    ) -> Optional[Ship24GetTrackerDetailResponse]:
        url = f"{SHIP_24_API_BASE_URL}/{tracker_id}/results"
        async with self.session.get(url, headers=self.headers) as response:
            if response.status in [200, 201]:
                response_json = await response.json()
                tracking_details = Ship24GetTrackerDetailResponse(**response_json["data"])
                return tracking_details
            else:
                log_warning(
                    "Could get Ship24 tracker results.",
                    courier=courier,
                    tracking_number=tracking_number,
                )
                return None
