"""Sensor platform for integration_blueprint."""  # noqa: EXE002

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import MidasDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import IntegrationMidasConfigEntry


# Each of these sensors is created for every configured rate id
SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="current",
        translation_key="current",
        icon="mdi:electric_meter",
    ),
    # TODO sensors for next 15 minutes, next hour
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
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = 4
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: MidasDataUpdateCoordinator,
        description: SensorEntityDescription,
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
            manufacturer="MIDAS",
            model=None,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return str(self.coordinator.data[self._rate_id].GetCurrentTariffs()[0].value)
