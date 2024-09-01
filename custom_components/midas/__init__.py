"""
Custom integration to integrate integration_blueprint with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/integration_blueprint
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .api import IntegrationMidasApiClient
from .const import (
    CONF_PASSWORD,
    CONF_RATEIDS,
    CONF_USERNAME,
    PLATFORMS,
)
from .coordinator import MidasDataUpdateCoordinator
from .data import IntegrationMidasData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import IntegrationMidasConfigEntry


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: IntegrationMidasConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = MidasDataUpdateCoordinator(
        hass=hass,
        client=IntegrationMidasApiClient(
            hass=hass,
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
        ),
    )
    entry.runtime_data = IntegrationMidasData(
        coordinator=coordinator,
        rate_ids=entry.data[CONF_RATEIDS],
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    # Call async_setup_entry for the provided platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: IntegrationMidasConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: IntegrationMidasConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
