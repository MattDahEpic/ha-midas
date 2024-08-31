"""Config flows for MIDAS."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from california_midasapi.exception import (
    MidasAuthenticationError,
    MidasClientError,
    MidasCommunicationError,
)
from homeassistant import config_entries, data_entry_flow

from .api import IntegrationMidasApiClient
from .const import (
    CONF_PASSWORD,
    CONF_RATEIDS,
    CONF_USERNAME,
    CONFIG_SCHEMA_CREDENTIALS,
    CONFIG_SCHEMA_OPTIONS,
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
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    hass=self.hass,
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except MidasAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except MidasCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except MidasClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                # Move onto step 2
                self.credential_data = user_input  # Store info to use in next step
                return await self.async_step_options()  # Start the next step

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA_CREDENTIALS,
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
