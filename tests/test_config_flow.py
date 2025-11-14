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


async def test_config_show_form(hass: HomeAssistant) -> None:
    """Test that the first step menu is served when there's no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER


async def test_config_create_account_clientside_validation(
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


async def test_config_create_account_invalid_credentials(
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


async def test_config_create_account_valid_credentials(
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


async def test_config_existing_account_clientside_validation(
    hass: HomeAssistant,
) -> None:
    """Test that providing no account details gives an error."""
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER
    # login
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "auth"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "auth"
    # test invalid details
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "",
            CONF_PASSWORD: "",
        },
    )
    assert result["errors"].get("base") == "auth"
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "auth"


async def test_config_existing_account_invalid_credentials(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that providing invalid account details gives an error."""
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER
    # login
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "auth"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "auth"
    # test invalid details
    error_text = "Invalid Username/Password combination."
    aioclient_mock.get(
        "https://midasapi.energy.ca.gov/api/token",
        status=HTTPStatus.UNAUTHORIZED,
        text=error_text,
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "test",
            CONF_PASSWORD: "test",
        },
    )
    assert result["errors"].get("base") == "auth"
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "auth"


async def test_config_existing_account_connection_error(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that the user gets a unique error message when a connection failure occurs while logging in."""  # noqa: E501
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER
    # login
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "auth"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "auth"
    # test invalid details
    aioclient_mock.get("https://midasapi.energy.ca.gov/api/token", exc=TimeoutError())
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "test",
            CONF_PASSWORD: "test",
        },
    )
    assert result["errors"].get("base") == "connection"
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "auth"


async def test_config_existing_account_valid_credentials(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that providing valid account details moves to the next step."""
    # have account? menu
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == SOURCE_USER
    # login
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "auth"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "auth"
    # test valid details
    aioclient_mock.get(
        "https://midasapi.energy.ca.gov/api/token",
        status=HTTPStatus.OK,
        text="Token issued and will expire in 10 minutes.",
        headers={"Content-Type": "text/plain; charset=utf-8", "Token": "fake_token"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "test",
            CONF_PASSWORD: "test",
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "options"
