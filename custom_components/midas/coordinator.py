"""DataUpdateCoordinator for MIDAS."""

from __future__ import annotations

from datetime import datetime, timedelta
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
    cached_data: dict[str, RateInfo]
    last_update_time: datetime | None

    def __init__(
        self,
        hass: HomeAssistant,
        client: IntegrationMidasApiClient,
    ) -> None:
        """Initialize."""
        self._client = client
        self.cached_data = {}
        self.last_update_time = None

        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            # Have the coordinator update the entities every minute,
            # but we only get the real data at startup and every hour
            update_interval=timedelta(seconds=60),
            always_update=True,
        )

    async def _async_update_data(self) -> Any:
        """Return cached data, updating it if absent or stale."""
        if len(self.cached_data) == 0 or self.last_update_time is None:
            # Update the cached data if there is none
            await self._async_update_cached_data()
        if datetime.now() - self.last_update_time > timedelta(minutes=60):  # type: ignore None bc last update time is not None here # noqa: DTZ005
            # Update again if we haven't updated in an hour
            await self._async_update_cached_data()

        return self.cached_data

    async def _async_update_cached_data(self) -> None:
        """Update the cached data."""
        self.cached_data = {}
        try:
            for rid in self.config_entry.runtime_data.rate_ids:
                self.cached_data[rid] = await self._client.async_get_rate_data(rid)
                # Call GetCurrentTariffs to cache parsed start and end times
                # Makes getting the active tariffs for each sensor much faster
                tariffs = self.cached_data[rid].GetCurrentTariffs()
                # Check if there are any tariffs and issue error if not
                if len(tariffs) == 0:
                    LOGGER.error(
                        f"Rate ID {rid} has no active tariffs! This may mean the utility has changed Rate IDs or has simply stopped submitting data to MIDAS. Check your latest bill for a new Rate ID. If this persists, please reach out to your utility and tell them the Rate ID on your bill is not returning any data for your smart home system to use."  # noqa: E501
                    )
            self.last_update_time = datetime.now()  # noqa: DTZ005
        except MidasAuthenticationException as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MidasException as exception:
            raise UpdateFailed(exception) from exception
