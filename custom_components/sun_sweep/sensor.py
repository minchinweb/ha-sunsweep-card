# Copyright (c) 2026 MinchinWeb
"""Whether the sun is up, plus the sunrise and sunset azimuths."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import DEGREE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .constants import ABOVE, BELOW, DOMAIN
from .coordinator import SunSweepConfigEntry, SunSweepCoordinator

PARALLEL_UPDATES = 0

# key, name, icon
_AZIMUTHS = (
    ("sunrise_azimuth", "Sunrise azimuth", "mdi:weather-sunset-up"),
    ("sunset_azimuth", "Sunset azimuth", "mdi:weather-sunset-down"),
)


def _device_info(coordinator: SunSweepCoordinator) -> DeviceInfo:
    entry = coordinator.config_entry
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SunSweepConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sweep sensor and the two horizon azimuths."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            SunSweepSensor(coordinator),
            *(AzimuthSensor(coordinator, *item) for item in _AZIMUTHS),
        ]
    )


class SunSweepSensor(CoordinatorEntity[SunSweepCoordinator], SensorEntity):
    """``above_horizon`` or ``below_horizon``, with the drawing in its attributes."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:sun-compass"

    def __init__(self, coordinator: SunSweepCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self) -> str:
        if self.coordinator.data["sun_elevation"] > 0:
            return ABOVE
        return BELOW

    @property
    def extra_state_attributes(self) -> dict:
        return self.coordinator.data


class AzimuthSensor(CoordinatorEntity[SunSweepCoordinator], SensorEntity):
    """One edge of today's daylight, in degrees clockwise from north."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = DEGREE
    _attr_state_class = SensorStateClass.MEASUREMENT_ANGLE
    _attr_suggested_display_precision = 1

    def __init__(
        self, coordinator: SunSweepCoordinator, key: str, name: str, icon: str
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self._key)
        if value is None:
            return None
        return float(value)
