"""Midas API Client."""  # noqa: EXE002

from __future__ import annotations

from typing import TYPE_CHECKING

from california_midasapi import Midas

if TYPE_CHECKING:
    from california_midasapi.ratelist import RateInfo
    from homeassistant.core import HomeAssistant


class IntegrationMidasApiClient:
    """Midas API Client."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
    ) -> None:
        """Midas API Client."""
        self._hass = hass
        self._midas = Midas(username, password)

    async def async_get_rate_data(self, rate_id: str) -> RateInfo:
        """Get data from the API."""
        return await self._hass.async_add_executor_job(self._midas.GetRateInfo, rate_id)

    async def async_test_credentials(self) -> None:
        """Check for validity of the set credentials. Throws if invalid."""
        await self._hass.async_add_executor_job(self._midas.test_credentials)
