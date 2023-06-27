from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from app.db.geocode_forward import GeocodeForwardModel
from app.db.short_address import ShortAddressModel
from app.external.geocode_client import GeoCoordinates
from app.external.openai_client import AddressParts
from app.external.ship24_client import (
    Ship24GetTrackerDetailResponse,
)
from app.services.tracking_service import TrackingService
from tests.unit.data.ship24_data import (
    ship24_response,
)
from tests.unit.data.tracking_service_data import (
    tracker_service_get_tracking_details_response,
)


class TrackingServiceTestCase(IsolatedAsyncioTestCase):
    @patch("app.db.ship24.Ship24Model.insert")
    @patch("app.db.ship24.Ship24ModelContext.get_by_courier_and_tracking_number")
    @pytest.mark.asyncio
    async def test_get_tracking_details_returns_none(self, mock_get_by_courier_and_tracking_number, mock_db_insert):
        mock_get_by_courier_and_tracking_number.return_value = None

        mock_ship24_client = AsyncMock()
        mock_ship24_client.get_tracker_results.return_value = Ship24GetTrackerDetailResponse(trackings=[])
        mock_geocode_client = MagicMock()
        mock_open_ai_client = MagicMock()
        service = TrackingService(mock_ship24_client, mock_geocode_client, mock_open_ai_client)
        res = await service.get_tracking_details("1234", "234235")
        self.assertIsNone(res)

    @patch("app.db.geocode_forward.GeocodeForwardModel.insert")
    @patch("app.db.geocode_forward.GeocodeForwardModelContext.find_by_address")
    @pytest.mark.asyncio
    async def test_get_geolocation_cache_miss(self, mock_find_by_address, mock_db_insert):
        mock_find_by_address.return_value = None

        model = {
            "latitude": 12,
            "longitude": 34,
            "display_name": "hello",
        }
        mock_ship24_client = MagicMock()
        mock_geocode_client = AsyncMock()
        mock_geocode_client.get_geo_coordinates.return_value = GeoCoordinates(**model)
        mock_open_ai_client = MagicMock()
        service = TrackingService(mock_ship24_client, mock_geocode_client, mock_open_ai_client)

        res = await service._get_geolocation("12345")
        self.assertEqual(res.latitude, model["latitude"])
        self.assertEqual(res.longitude, model["longitude"])
        self.assertEqual(res.display_name, model["display_name"])

        mock_db_insert.assert_called_once_with("12345", 12, 34, "hello")

    @patch("app.db.geocode_forward.GeocodeForwardModel.insert")
    @patch("app.db.geocode_forward.GeocodeForwardModelContext.find_by_address")
    @pytest.mark.asyncio
    async def test_get_geolocation_cache_hit(self, mock_find_by_address, mock_db_insert):
        model = GeocodeForwardModel()
        model.lat = 12
        model.lon = 34
        model.display_name = "hello"
        mock_find_by_address.return_value = model

        mock_ship24_client = MagicMock()
        mock_geocode_client = MagicMock()
        mock_open_ai_client = MagicMock()
        service = TrackingService(mock_ship24_client, mock_geocode_client, mock_open_ai_client)

        res = await service._get_geolocation("12345")
        self.assertEqual(res.latitude, model.lat)
        self.assertEqual(res.longitude, model.lon)
        self.assertEqual(res.display_name, model.display_name)

        mock_geocode_client.get_geo_coordinates.assert_not_called()
        mock_db_insert.assert_not_called()

    @patch("app.db.short_address.ShortAddressModel.insert")
    @patch("app.db.short_address.ShortAddressModelContext.find_by_address")
    @pytest.mark.asyncio
    async def test_get_short_address_cache_miss(self, mock_find_by_address, mock_db_insert):
        mock_find_by_address.return_value = None

        model = {
            "city": "sf",
            "state": "CA",
            "country": "USA",
        }
        mock_ship24_client = MagicMock()
        mock_geocode_client = MagicMock()
        mock_open_ai_client = AsyncMock()
        mock_open_ai_client.shorten_address.return_value = AddressParts(**model)

        service = TrackingService(mock_ship24_client, mock_geocode_client, mock_open_ai_client)

        service._get_geolocation = AsyncMock()
        service._get_geolocation.return_value = GeoCoordinates(
            **{
                "latitude": 12,
                "longitude": 34,
                "display_name": "hello",
            }
        )

        res = await service._get_short_address("12345")
        expected = "sf, CA, USA"
        self.assertEqual(res, expected)
        mock_db_insert.assert_called_once_with("12345", expected)
        mock_open_ai_client.shorten_address.assert_called_once_with("12345")

    @patch("app.db.short_address.ShortAddressModel.insert")
    @patch("app.db.short_address.ShortAddressModelContext.find_by_address")
    @pytest.mark.asyncio
    async def test_get_short_address_cache_hit(self, mock_find_by_address, mock_db_insert):
        expected = "sf, CA, USA"

        model = ShortAddressModel()
        model.address = "12345"
        model.short_address = expected
        mock_find_by_address.return_value = model

        mock_ship24_client = MagicMock()
        mock_geocode_client = MagicMock()
        mock_open_ai_client = MagicMock()
        service = TrackingService(mock_ship24_client, mock_geocode_client, mock_open_ai_client)

        res = await service._get_short_address("12345")
        self.assertEqual(res, expected)

        mock_geocode_client.get_geo_coordinates.assert_not_called()
        mock_db_insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_tracking_details(self):
        mock_ship24_client = MagicMock()
        mock_geocode_client = MagicMock()
        mock_open_ai_client = MagicMock()

        mock_open_ai_client.shorten_address.return_value = AddressParts(city="sf", state="ca", country="usa")

        service = TrackingService(mock_ship24_client, mock_geocode_client, mock_open_ai_client)
        service._get_tracker_info_from_ship24 = AsyncMock()
        service._get_tracker_info_from_ship24.return_value = Ship24GetTrackerDetailResponse(**ship24_response()["data"])

        service._get_geolocation = AsyncMock()
        service._get_geolocation.return_value = GeoCoordinates(
            **{
                "latitude": 12,
                "longitude": 34,
                "display_name": "hello",
            }
        )

        service._get_short_address = AsyncMock()
        service._get_short_address.return_value = "short_address"

        res = await service.get_tracking_details("DHL", "123456789")

        expected = tracker_service_get_tracking_details_response()
        self.assertEqual(res.tracker_id, expected["tracker_id"])
        self.assertEqual(res.tracking_number, expected["tracking_number"])
        self.assertEqual(res.last_event.location, "short_address")
        self.assertEqual(res.estimated_delivery_date, expected["estimated_delivery_date"])
