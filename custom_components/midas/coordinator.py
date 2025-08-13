"""DataUpdateCoordinator for MIDAS."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from california_midasapi.exception import MidasAuthenticationException, MidasException
from california_midasapi.types import RateInfo
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry
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
            # Only get new data from the server at startup and every hour
            update_interval=timedelta(hours=1),
            always_update=True,
        )

    async def _async_update_data(self) -> dict[str, RateInfo]:
        """Get the newsest set of rates."""
        data: dict[str, RateInfo] = {}
        try:
            for rid in self.config_entry.runtime_data.rate_ids:
                data[rid] = await self._client.async_get_rate_data(rid)
                # Call GetCurrentTariffs to cache parsed start and end times
                # Makes getting the active tariffs for each sensor much faster
                tariffs = data[rid].GetCurrentTariffs()
                # Check if there are any tariffs and issue error if not
                if len(tariffs) == 0:
                    issue_registry.async_create_issue(
                        self.hass,
                        DOMAIN,
                        f"no_tarrifs_{rid.lower()}",
                        is_fixable=False,
                        is_persistent=False,
                        severity=issue_registry.IssueSeverity.ERROR,
                        translation_key="no_tariffs",
                        translation_placeholders={"rid": rid},
                    )
                    LOGGER.debug(
                        f"Rate ID {rid} has no active tariffs! An issue was created."
                    )
                else:
                    issue_registry.async_delete_issue(
                        self.hass,
                        DOMAIN,
                        f"no_tarrifs_{rid.lower()}",
                    )
        except MidasAuthenticationException as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MidasException as exception:
            raise UpdateFailed(exception) from exception
        else:
            # Update sensors immediately when we get new data
            self.async_update_listeners()
            return data
