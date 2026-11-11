# Copyright (c) 2026 MinchinWeb
"""What House Structure says about the building outline."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .constants import HOUSE_STRUCTURE, OUTLINE_SENSOR


def outline_status(hass: HomeAssistant) -> str | None:
    """The state of House Structure's Building outline sensor.

    Returns:
        ``found``, ``not_found``, ``failed`` or ``not_loaded``, or ``None``
        when House Structure is missing, is too old to have the sensor, or
        the sensor has no state yet.
    """
    registry = er.async_get(hass)
    for entry in hass.config_entries.async_entries(HOUSE_STRUCTURE):
        entity_id = registry.async_get_entity_id(
            "sensor", HOUSE_STRUCTURE, OUTLINE_SENSOR.format(entry.entry_id)
        )
        state = hass.states.get(entity_id) if entity_id else None
        if state is not None and state.state not in ("unknown", "unavailable"):
            return state.state
    return None
