"""Test the MIDAS config flow."""

# ignore errors that shouldn't matter in this test file
# pyright: reportTypedDictNotRequiredAccess=false
# ruff: noqa: S101

from http import HTTPStatus

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.midas.const import (
    CONF_EMAIL,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
)


async def test_show_form(hass: HomeAssistant) -> None:
    """Test that the first step menu is served when there's no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER


async def test_user_config_create_account_clientside_validation(
    hass: HomeAssistant,
) -> None:
    """Test that the user gets an error when not providing any credentials."""
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER
    # create account
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "register"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "register"
    # test invalid details
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "",
            CONF_PASSWORD: "",
            CONF_EMAIL: "",
            CONF_NAME: "",
        },
    )
    assert result["errors"].get("base") == "registration_invalid"
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "register"


async def test_user_config_create_account_invalid_credentials(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that the user gets the server-side error back when providing invalid credentials."""
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER
    # create account
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "register"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "register"
    # test valid details
    error_text = "Registration Error: Password does not meet the following requirements: Uppercase letters must be greater than or equal to 1;Numeric characters must be greater than or equal to 1;Special characters must be greater than or equal to 1;Password length must be greater than or equal to 15"
    aioclient_mock.post(
        "https://midasapi.energy.ca.gov/api/registration",
        status=HTTPStatus.BAD_REQUEST,
        text=error_text,
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "username",
            CONF_PASSWORD: "password",
            CONF_EMAIL: "test@example.com",
            CONF_NAME: "Test User",
        },
    )
    assert result["errors"].get("base") == "error_with_detail"
    assert result["description_placeholders"].get("error_detail") == error_text
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "register"


async def test_user_config_create_account_valid_credentials(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that the user can create an account."""
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER
    # create account
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "register"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "register"
    # test valid details
    aioclient_mock.post(
        "https://midasapi.energy.ca.gov/api/registration",
        status=HTTPStatus.OK,
        text="something about clicking the link, i don't want to create another account to get the exact text. 200 status is what matters",  # noqa: E501
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "username",
            CONF_PASSWORD: "password",
            CONF_EMAIL: "test@example.com",
            CONF_NAME: "Test User",
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "register_result"


# TODO test existing account
# TODO test valid and invalid rins
# TODO test reconfigure
