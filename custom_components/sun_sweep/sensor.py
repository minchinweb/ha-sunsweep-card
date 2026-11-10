# Copyright (c) 2026 MinchinWeb
"""One sensor: whether the sun is up, and the geometry the card draws."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .constants import ABOVE, BELOW, DOMAIN
from .coordinator import SunSweepConfigEntry, SunSweepCoordinator

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SunSweepConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sweep sensor."""
    async_add_entities([SunSweepSensor(entry.runtime_data)])


class SunSweepSensor(CoordinatorEntity[SunSweepCoordinator], SensorEntity):
    """``above_horizon`` or ``below_horizon``, with the drawing in its attributes."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:sun-compass"

    def __init__(self, coordinator: SunSweepCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str:
        if self.coordinator.data["sun_elevation"] > 0:
            return ABOVE
        return BELOW

    @property
    def extra_state_attributes(self) -> dict:
        return self.coordinator.data
