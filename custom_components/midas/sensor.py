"""Sensor platform for the MIDAS integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import MidasDataUpdateCoordinator

if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal

    from california_midasapi.types import RateInfo, ValueInfoItem
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

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

    tariffs_fn: Callable[[RateInfo], list[ValueInfoItem]] = (
        lambda rate: rate.GetCurrentTariffs()
    )
    """Function to get the current tariffs."""

    value_fn: Callable[
        [RateInfo, ValueInfoItem], StateType | date | datetime | Decimal
    ] = lambda _, tariff: tariff.value
    """Function to get the value of the sensor.
    Receives the rate info and the current tariff."""

    def unique_id_fn(self, rate_id: str) -> str:
        """Return a unique id for the entity."""
        return f"{rate_id}_{self.key}"


# Each of these sensors is created for every configured rate id
SENSOR_DESCRIPTIONS: tuple[MidasSensorEntityDescription, ...] = (
    MidasSensorEntityDescription(
        key="current",
        translation_key="current",
        icon="mdi:meter-electric",
        native_unit_of_measurement="USD/kWh",
        suggested_display_precision=5,
    ),
    MidasSensorEntityDescription(
        key="current_tariff_name",
        translation_key="current_tariff_name",
        icon="mdi:text",
        entity_registry_enabled_default=False,
        value_fn=lambda _, tariff: tariff.ValueName,
    ),
    MidasSensorEntityDescription(
        key="current_tariff_start",
        translation_key="current_tariff_start",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda _, tariff: tariff.GetStart(),
    ),
    MidasSensorEntityDescription(
        key="current_tariff_end",
        translation_key="current_tariff_end",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda _, tariff: tariff.GetEnd(),
    ),
    MidasSensorEntityDescription(
        key="15min",
        translation_key="15min",
        icon="mdi:meter-electric",
        native_unit_of_measurement="USD/kWh",
        suggested_display_precision=5,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(minutes=15)  # noqa: DTZ005
        ),
    ),
    MidasSensorEntityDescription(
        key="15min_tariff_name",
        translation_key="15min_tariff_name",
        icon="mdi:text",
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(minutes=15)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.ValueName,
    ),
    MidasSensorEntityDescription(
        key="15min_tariff_start",
        translation_key="15min_tariff_start",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(minutes=15)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.GetStart(),
    ),
    MidasSensorEntityDescription(
        key="15min_tariff_end",
        translation_key="15min_tariff_end",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(minutes=15)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.GetEnd(),
    ),
    MidasSensorEntityDescription(
        key="1hour",
        translation_key="1hour",
        icon="mdi:meter-electric",
        native_unit_of_measurement="USD/kWh",
        suggested_display_precision=5,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(hours=1)  # noqa: DTZ005
        ),
    ),
    MidasSensorEntityDescription(
        key="1hour_tariff_name",
        translation_key="1hour_tariff_name",
        icon="mdi:text",
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(hours=1)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.ValueName,
    ),
    MidasSensorEntityDescription(
        key="1hour_tariff_start",
        translation_key="1hour_tariff_start",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(hours=1)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.GetStart(),
    ),
    MidasSensorEntityDescription(
        key="1hour_tariff_end",
        translation_key="1hour_tariff_end",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(hours=1)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.GetEnd(),
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
        self._attr_unique_id = description.unique_id_fn(self._rate_id)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._rate_id)},
            name=self._rate_id,
            manufacturer=None,
            model=None,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the native value of the sensor."""
        rate = self.coordinator.data[self._rate_id]
        tariffs = self.entity_description.tariffs_fn(rate)
        if len(tariffs) == 0:
            # No tariffs! Logging for this event is handled by the coordinator.
            return None
        tariff = tariffs[0]
        return self.entity_description.value_fn(rate, tariff)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Extra data for the sensor."""
        rate = self.coordinator.data[self._rate_id]
        tariffs = self.entity_description.tariffs_fn(rate)
        if len(tariffs) == 0:
            # No tariffs! Logging for this event is handled by the coordinator.
            return None
        tariff = tariffs[0]
        return {
            DATA_RATE_NAME: rate.RateName,
            DATA_RATE_TYPE: rate.RateType,
            DATA_RATE_URL: rate.RatePlan_Url,
            DATA_TARIFF_NAME: tariff.ValueName,
            DATA_START_TIME: tariff.GetStart(),
            DATA_END_TIME: tariff.GetEnd(),
        }

    @property
    def available(self) -> bool:
        """Returns if the sensor is available."""
        return super().available and (self.native_value is not None)
