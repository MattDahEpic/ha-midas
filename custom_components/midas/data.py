"""Custom types for integration_blueprint."""  # noqa: EXE002

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import MidasDataUpdateCoordinator


type IntegrationMidasConfigEntry = ConfigEntry[IntegrationMidasData]


@dataclass
class IntegrationMidasData:
    """Data for the MIDAS integration."""

    coordinator: MidasDataUpdateCoordinator
    rate_ids: list[str]
