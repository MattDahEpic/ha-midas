"""Config flows for MIDAS."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from california_midasapi.authentication import Midas as MidasAuth
from california_midasapi.exception import (
    MidasAuthenticationException,
    MidasCommunicationException,
    MidasException,
    MidasRegistrationException,
)
from homeassistant import config_entries, data_entry_flow

from .api import IntegrationMidasApiClient
from .const import (
    CONF_EMAIL,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RATEIDS,
    CONF_USERNAME,
    CONFIG_SCHEMA_AUTH,
    CONFIG_SCHEMA_OPTIONS,
    CONFIG_SCHEMA_REGISTER,
    DOMAIN,
    LOGGER,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class MidasFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,  # noqa: ARG002
    ) -> data_entry_flow.FlowResult:
        """First step."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["auth", "register"],  # Next step names
        )

    async def async_step_register(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Help the user register a new MIDAS account."""
        _errors = {}
        _description_placeholders = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            email = user_input[CONF_EMAIL]
            name = user_input[CONF_NAME]

            if (
                username is None
                or len(username) == 0
                or password is None
                or len(password) == 0
                or email is None
                or len(email) == 0
                or name is None
                or len(name) == 0
            ):
                _errors["base"] = "registration_invalid"

            if _errors == {}:  # No errors
                try:
                    await self.hass.async_add_executor_job(
                        MidasAuth.register, username, password, email, name
                    )
                except MidasRegistrationException as exception:
                    LOGGER.warning(exception)
                    # Show the error to the user, passing it through the translations
                    _errors["base"] = "error_with_detail"
                    _description_placeholders["error_detail"] = str(exception)
                except MidasException as exception:
                    LOGGER.exception(exception)
                    _errors["base"] = "unknown"
                else:
                    # Redirect to step that tells the user to click the link in their email  # noqa: E501
                    return await self.async_step_register_result()

        return self.async_show_form(
            step_id="register",
            data_schema=self.add_suggested_values_to_schema(
                CONFIG_SCHEMA_REGISTER, user_input
            ),
            errors=_errors,
            description_placeholders=_description_placeholders,
        )

    async def async_step_register_result(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """
        Step solely to show the result of creating a MIDAS account.

        Lets users know to click the link in their email.
        """
        if user_input is not None:  # User clicked submit
            # Transition to auth step
            return await self.async_step_auth()

        return self.async_show_form(step_id="register_result")

    async def async_step_auth(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Collect username and password."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    hass=self.hass,
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except MidasAuthenticationException as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except MidasCommunicationException as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except MidasException as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                # Move onto next step
                self.credential_data = user_input  # Store info to use in next step
                return await self.async_step_options()  # Start the next step

        return self.async_show_form(
            step_id="auth",
            data_schema=CONFIG_SCHEMA_AUTH,
            errors=_errors,
        )

    async def async_step_options(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle the second step of the flow."""
        _errors = {}
        if user_input is not None:
            for rid in user_input[CONF_RATEIDS]:
                if (
                    re.match("^[A-Z]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$", rid)
                    is None
                ):
                    _errors["base"] = "rateid_invalid"

            if _errors == {}:  # No errors
                # Pull in data from credentials step
                user_input.update(self.credential_data)
                # Create entry with combined data
                return self.async_create_entry(
                    title=f"MIDAS Account: {user_input[CONF_USERNAME]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="options",
            data_schema=CONFIG_SCHEMA_OPTIONS,
            errors=_errors,
        )

    async def _test_credentials(
        self, hass: HomeAssistant, username: str, password: str
    ) -> None:
        """Validate credentials."""
        client = IntegrationMidasApiClient(
            hass=hass,
            username=username,
            password=password,
        )
        await client.async_test_credentials()
