"""Sensor platform for the MIDAS integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import MidasDataUpdateCoordinator

if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal

    from california_midasapi.types import RateInfo, ValueInfoItem
    from homeassistant.core import CALLBACK_TYPE, HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .data import IntegrationMidasConfigEntry

DATA_RATE_NAME = "rate_name"
DATA_RATE_TYPE = "rate_type"
DATA_RATE_URL = "rate_url"
DATA_TARIFF_NAME = "tariff_name"
DATA_START_TIME = "start_time"
DATA_END_TIME = "end_time"
DATA_UPDATE_LOOP_NEXT_TIME = "update_loop_next_time"


@dataclass(frozen=True, kw_only=True)
class MidasSensorEntityDescription(SensorEntityDescription):
    """Describes MIDAS sensors."""

    offset_fn: Callable[[RateInfo], timedelta] = lambda _: timedelta()
    """Function to get the offset from the current time this sensor applies to.

    Used in `rate.GetActiveTariffs()` to get the tariff to pass into `value_fn`."""

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
        offset_fn=lambda _: timedelta(minutes=15),
    ),
    MidasSensorEntityDescription(
        key="15min_tariff_name",
        translation_key="15min_tariff_name",
        icon="mdi:text",
        entity_registry_enabled_default=False,
        offset_fn=lambda _: timedelta(minutes=15),
        value_fn=lambda _, tariff: tariff.ValueName,
    ),
    MidasSensorEntityDescription(
        key="15min_tariff_start",
        translation_key="15min_tariff_start",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        offset_fn=lambda _: timedelta(minutes=15),
        value_fn=lambda _, tariff: tariff.GetStart(),
    ),
    MidasSensorEntityDescription(
        key="15min_tariff_end",
        translation_key="15min_tariff_end",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        offset_fn=lambda _: timedelta(minutes=15),
        value_fn=lambda _, tariff: tariff.GetEnd(),
    ),
    MidasSensorEntityDescription(
        key="1hour",
        translation_key="1hour",
        icon="mdi:meter-electric",
        native_unit_of_measurement="USD/kWh",
        suggested_display_precision=5,
        offset_fn=lambda _: timedelta(hours=1),
    ),
    MidasSensorEntityDescription(
        key="1hour_tariff_name",
        translation_key="1hour_tariff_name",
        icon="mdi:text",
        entity_registry_enabled_default=False,
        offset_fn=lambda _: timedelta(hours=1),
        value_fn=lambda _, tariff: tariff.ValueName,
    ),
    MidasSensorEntityDescription(
        key="1hour_tariff_start",
        translation_key="1hour_tariff_start",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        offset_fn=lambda _: timedelta(hours=1),
        value_fn=lambda _, tariff: tariff.GetStart(),
    ),
    MidasSensorEntityDescription(
        key="1hour_tariff_end",
        translation_key="1hour_tariff_end",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        offset_fn=lambda _: timedelta(hours=1),
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

    _update_loop_callback_removal_callback: CALLBACK_TYPE
    _update_loop_next_time: datetime | None = None

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

    async def async_added_to_hass(self) -> None:
        """Callback for initial sensor creation, starts internal update loop."""  # noqa: D401
        await super().async_added_to_hass()
        # Start our own internal update loop so we update right on the tariff changeover
        await self._async_update_loop(datetime.now())  # noqa: DTZ005
        # Cancel the update loop on the destruction of this sensor
        self.async_on_remove(self._update_loop_callback_removal_callback)

    async def _async_update_loop(self, now: datetime) -> None:
        """Update the current sensor and schedules this function to run again at the beginning of the next tariff."""  # noqa: E501
        # Update this sensor
        self.async_write_ha_state()

        # Schedule the next update right after the end of the current tariff
        rate = self.coordinator.data[self._rate_id]
        offset = self.entity_description.offset_fn(rate)
        tariffs = rate.GetActiveTariffs(datetime.now() + offset)  # noqa: DTZ005

        next_update = now + timedelta(hours=1)  # failsafe hourly update for no tariffs
        if len(tariffs) > 0:
            # add 1 second to get to the first second of the next tariff
            # we want the 15 minute sensor to update 15 minutes before the end of the
            #   tariff so subtract the offset
            # the hour sensor will already be on the end of the next tariff so
            #   subtracting an hour from it will still be an hour from now
            next_update = (tariffs[0].GetEnd() + timedelta(seconds=1)) - offset
        self._update_loop_callback_removal_callback = async_track_point_in_time(
            self.hass, self._async_update_loop, next_update
        )
        self._update_loop_next_time = next_update
        self.async_write_ha_state()  # Update again to get next loop attribute updated

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the native value of the sensor."""
        rate = self.coordinator.data[self._rate_id]
        offset = self.entity_description.offset_fn(rate)
        tariffs = rate.GetActiveTariffs(datetime.now() + offset)  # noqa: DTZ005
        if len(tariffs) == 0:
            # No tariffs! Logging for this event is handled by the coordinator.
            return None
        tariff = tariffs[0]
        return self.entity_description.value_fn(rate, tariff)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Extra data for the sensor."""
        rate = self.coordinator.data[self._rate_id]
        offset = self.entity_description.offset_fn(rate)
        tariffs = rate.GetActiveTariffs(datetime.now() + offset)  # noqa: DTZ005
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
            DATA_UPDATE_LOOP_NEXT_TIME: self._update_loop_next_time,
        }

    @property
    def available(self) -> bool:
        """Returns if the sensor is available."""
        return super().available and (self.native_value is not None)
