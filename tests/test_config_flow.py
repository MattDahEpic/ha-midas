"""Test the MIDAS config flow."""

# ignore errors that shouldn't matter in this test file
# pyright: reportTypedDictNotRequiredAccess=false
# ruff: noqa: S101

from http import HTTPStatus
from unittest.mock import AsyncMock

from aiohttp import ServerTimeoutError
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.midas.config_flow import MidasFlowHandler
from custom_components.midas.const import (
    CONF_RATEIDS,
    DOMAIN,
)


async def test_config_show_form(hass: HomeAssistant) -> None:
    """Test that the first step form is served when there's no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER


async def test_config_rateids_no_rateids(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that configuring requires at least one RIN."""
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER
    # test empty rateids
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_RATEIDS: [],
        },
    )
    assert result["errors"].get("base") == "rateids_missing"
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER


async def test_config_rateids_invalid_rateids(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that providing invalid rateids gives an error."""
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER
    # test empty rateids
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_RATEIDS: ["TEST-WRONG-FORMAT"],
        },
    )
    assert result["errors"].get("base") == "rateid_invalid"
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER


async def test_config_rateids_valid_rateids(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test that providing valid rateids completes the configuration."""
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER
    # test empty rateids
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_RATEIDS: ["TEST-TEST-TEST-TEST"],
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "MIDAS"
    assert result["data"].get(CONF_RATEIDS) == ["TEST-TEST-TEST-TEST"]
    assert len(mock_setup_entry.mock_calls) == 1


async def test_config_reconfigure_no_rateids(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that reconfiguring still requires at least one RIN."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # start reconfigure flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_config_entry.entry_id},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_RECONFIGURE
    # test empty rateids
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_RATEIDS: [],
        },
    )
    assert result["errors"].get("base") == "rateids_missing"
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_RECONFIGURE


async def test_config_reconfigure_invalid_rateids(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that reconfiguring with invalid rate ids presents an error."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # start reconfigure flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_config_entry.entry_id},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_RECONFIGURE
    # test empty rateids
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_RATEIDS: ["TEST-WRONG-FORMAT"],
        },
    )
    assert result["errors"].get("base") == "rateid_invalid"
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_RECONFIGURE


async def test_config_reconfigure_valid_rateids(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that reconfiguring with valid rateids works."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # start reconfigure flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_config_entry.entry_id},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == SOURCE_RECONFIGURE
    # test empty rateids
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_RATEIDS: ["TEST-TEST-TEST-NEW1"],
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    updated_entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    assert updated_entry.data[CONF_RATEIDS] == ["TEST-TEST-TEST-NEW1"]


async def test_rateid_validity_check() -> None:
    """Test the internal rate id validity check."""
    config_flow = MidasFlowHandler()

    valid_ids = [
        "USCA-PGXX-0400-0000",
        "USCA-PGXX-0200-0000",
        "USCA-SCSC-0400-0000",
        "USCA-XXSF-0063-0000",
        "USCA-SCSC-0500-0000",
        "USCA-XXMB-0026-SCE",
    ]
    assert not config_flow._test_rateids(valid_ids)  # noqa: SLF001

    invalid_ids = ["TEST-WRONG-FORMAT"]
    assert config_flow._test_rateids(invalid_ids)  # noqa: SLF001
