"""Sensor platform for the MIDAS integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import MidasDataUpdateCoordinator

if TYPE_CHECKING:
    from collections.abc import Callable

    from california_midasapi.types import RateInfo, ValueInfoItem
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import IntegrationMidasConfigEntry

DATA_RATE_NAME = "rate_name"
DATA_RATE_TYPE = "rate_type"
DATA_RATE_URL = "rate_url"
DATA_TARIFF_NAME = "tariff_name"
DATA_START_TIME = "start_time"
DATA_END_TIME = "end_time"


@dataclass(frozen=True, kw_only=True)
class MidasSensorEntityDescription(SensorEntityDescription):
    """Describes MIDAS sensors."""

    rate_fn: Callable[[RateInfo], ValueInfoItem]


# Each of these sensors is created for every configured rate id
SENSOR_DESCRIPTIONS: tuple[MidasSensorEntityDescription, ...] = (
    MidasSensorEntityDescription(
        key="current",
        translation_key="current",
        icon="mdi:meter-electric",
        rate_fn=lambda rate: rate.GetCurrentTariffs()[0],
    ),
    MidasSensorEntityDescription(
        key="15min",
        translation_key="15min",
        icon="mdi:meter-electric",
        rate_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(minutes=15)  # noqa: DTZ005
        )[0],
    ),
    MidasSensorEntityDescription(
        key="1hour",
        translation_key="1hour",
        icon="mdi:meter-electric",
        rate_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(hours=1)  # noqa: DTZ005
        )[0],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: IntegrationMidasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        [
            MidasPriceSensor(
                coordinator=entry.runtime_data.coordinator,
                description=description,
                rate_id=rate_id,
            )  # Create a sensor
            for description in SENSOR_DESCRIPTIONS  # For each time offset
            for rate_id in entry.runtime_data.rate_ids  # For each configured rate id
        ]
    )


class MidasPriceSensor(CoordinatorEntity[MidasDataUpdateCoordinator], SensorEntity):
    """MIDAS Price Sensor class."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "USD/kWh"
    _attr_suggested_display_precision = 5
    _attr_attribution = ATTRIBUTION

    entity_description: MidasSensorEntityDescription

    def __init__(
        self,
        coordinator: MidasDataUpdateCoordinator,
        description: MidasSensorEntityDescription,
        rate_id: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator=coordinator)

        self.entity_description = description
        self._rate_id = rate_id
        self._attr_unique_id = f"{self._rate_id}_{description.key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._rate_id)},
            name=self._rate_id,
            manufacturer=None,
            model=None,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return str(
            self.entity_description.rate_fn(self.coordinator.data[self._rate_id]).value
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Extra data for the sensor."""
        rate = self.coordinator.data[self._rate_id]
        tariff = self.entity_description.rate_fn(rate)
        return {
            DATA_RATE_NAME: rate.RateName,
            DATA_RATE_TYPE: rate.RateType,
            DATA_RATE_URL: rate.RatePlan_Url,
            DATA_TARIFF_NAME: tariff.ValueName,
            DATA_START_TIME: tariff.GetStart(),
            DATA_END_TIME: tariff.GetEnd(),
        }
