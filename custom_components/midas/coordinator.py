"""DataUpdateCoordinator for MIDAS."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from california_midasapi.exception import MidasAuthenticationException, MidasException
from california_midasapi.types import RateInfo
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .api import (
        IntegrationMidasApiClient,
    )
    from .data import IntegrationMidasConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class MidasDataUpdateCoordinator(DataUpdateCoordinator[dict[str, RateInfo]]):
    """Class to manage fetching data from the API."""

    config_entry: IntegrationMidasConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: IntegrationMidasApiClient,
    ) -> None:
        """Initialize."""
        self._client = client

        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        data: dict[str, RateInfo] = {}
        try:
            for rid in self.config_entry.runtime_data.rate_ids:
                data[rid] = await self._client.async_get_rate_data(rid)
                # Call GetCurrentTariffs to cache parsed start and end times
                # Makes getting the active tariffs for each sensor much faster
                data[rid].GetCurrentTariffs()
        except MidasAuthenticationException as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MidasException as exception:
            raise UpdateFailed(exception) from exception
        else:
            return data
