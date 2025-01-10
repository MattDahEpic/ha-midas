"""Test the MIDAS config flow."""

from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.midas.const import (
    CONF_EMAIL,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RATEIDS,
    CONF_USERNAME,
    DOMAIN,
)


async def test_show_form(hass: HomeAssistant) -> None:
    """Test that the first step menu is served when there's no input"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER


