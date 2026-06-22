"""Constants for midas."""

from logging import Logger, getLogger

import voluptuous as vol
from homeassistant.const import Platform
from homeassistant.helpers import selector

LOGGER: Logger = getLogger(__package__)

DOMAIN = "midas"
ATTRIBUTION = "Data provided by https://midasapi.energy.ca.gov/"

"""Platforms provided by this integration."""
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]

# Config item variables
CONF_RATEIDS = "rate_ids"

CONFIG_SCHEMA_OPTIONS = vol.Schema(
    {
        vol.Required(CONF_RATEIDS): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT, multiple=True
            )
        )
    }
)

CONFIG_SCHEMA_RECONFIGURE = vol.Schema(
    {
        vol.Required(CONF_RATEIDS): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT, multiple=True
            )
        )
    }
)
