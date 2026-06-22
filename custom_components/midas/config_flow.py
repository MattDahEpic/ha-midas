"""Config flows for MIDAS."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from homeassistant import config_entries, data_entry_flow
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_RATEIDS,
    CONFIG_SCHEMA_OPTIONS,
    CONFIG_SCHEMA_RECONFIGURE,
    DOMAIN,
    LOGGER,
)
from .sensor import SENSOR_DESCRIPTIONS


class MidasFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for MIDAS."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle the first step of the flow."""
        _errors = {}
        if user_input is not None:
            if len(user_input[CONF_RATEIDS]) == 0:
                _errors["base"] = "rateids_missing"

            if self._test_rateids(user_input[CONF_RATEIDS]):
                _errors["base"] = "rateid_invalid"

            if _errors == {}:  # No errors
                # Create entry with combined data
                return self.async_create_entry(
                    title="MIDAS",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA_OPTIONS,
            errors=_errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Step to reconfigure this config entry."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        _errors = {}
        if TYPE_CHECKING:
            assert entry is not None

        if user_input is not None:
            if len(user_input[CONF_RATEIDS]) == 0:
                _errors["base"] = "rateids_missing"

            if self._test_rateids(user_input[CONF_RATEIDS]):
                _errors["base"] = "rateid_invalid"

            if _errors == {}:  # No errors
                await self.hass.config_entries.async_unload(entry.entry_id)
                # Assemble new data
                data = {**entry.data, **user_input}
                # Remove orphan devices that were from removed rates
                new_rateids = set(data[CONF_RATEIDS])
                old_rateids = set(entry.data[CONF_RATEIDS])
                for removed_rateid in old_rateids - new_rateids:
                    await self._purge_registries_for_rateid(removed_rateid)
                # Update saved data and reload
                self.hass.config_entries.async_update_entry(entry, data=data)
                await self.hass.config_entries.async_setup(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                CONFIG_SCHEMA_RECONFIGURE,
                entry.data,
            ),
            errors=_errors,
        )

    def _test_rateids(self, rate_ids: list[str]) -> bool:
        """
        Test a list of rate ids to ensure they are valid.

        Returns True if invalid, False if all are valid.
        """
        for rid in rate_ids:
            if (
                re.match("^[A-Z]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{3,4}$", rid)
                is None
            ):
                return True
        return False

    async def _purge_registries_for_rateid(self, rate_id: str) -> None:
        """Remove devices and entities for the specified rate id."""
        LOGGER.debug(f"Purging entities and devices for rate id {rate_id}")

        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)
        # remove entities
        entity_uniqueids = [
            entity_registry.async_get_entity_id(
                DOMAIN, "sensor", entity.unique_id_fn(rate_id)
            )
            for entity in SENSOR_DESCRIPTIONS
        ]
        for entity_id in entity_uniqueids:
            if entity_id is not None:
                entity_registry.async_remove(entity_id)
        # remove devices
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, rate_id)}  # defined in sensor.py
        )
        if device is not None:
            device_registry.async_remove_device(device.id)
