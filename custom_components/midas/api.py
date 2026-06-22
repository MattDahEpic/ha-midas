"""Midas API Client."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from california_midasapi import Midas
from homeassistant.helpers.aiohttp_client import async_get_clientsession

if TYPE_CHECKING:
    from california_midasapi.ratelist import RateInfo
    from homeassistant.core import HomeAssistant


class IntegrationMidasApiClient:
    """Midas API Client."""

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Midas API Client."""
        self._hass = hass
        self._midas = Midas(async_get_clientsession(hass))

    async def async_get_rate_data(self, rate_id: str) -> RateInfo:
        """Get data from the API."""
        return await self._midas.GetRateInfo(rate_id)

    async def async_get_historical_rate_data(self, rate_id: str) -> RateInfo:
        """Get historical data from the API."""
        now = datetime.now()  # noqa: DTZ005
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        return await self._midas.GetHistoricalRateInfo(rate_id, yesterday, tomorrow)
