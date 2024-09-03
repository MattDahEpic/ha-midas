"""Constants for midas."""

from logging import Logger, getLogger

import voluptuous as vol
from homeassistant.const import (
    CONF_EMAIL,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
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

# Config schemas
CONFIG_SCHEMA_REGISTER = vol.Schema(
    {
        vol.Required(CONF_USERNAME): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT,
            ),
        ),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.PASSWORD,
            ),
        ),
        vol.Required(CONF_EMAIL): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT,
            ),
        ),
        vol.Required(CONF_NAME): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT,
            ),
        ),
    }
)

CONFIG_SCHEMA_AUTH = vol.Schema(
    {
        vol.Required(CONF_USERNAME): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT,
            ),
        ),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.PASSWORD,
            ),
        ),
    },
)

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
