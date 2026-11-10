# Copyright (c) 2026 MinchinWeb
"""The sensor's attributes, including a home with no building outline."""

from __future__ import annotations

from datetime import datetime
import math
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sun_sweep.constants import ABOVE, BELOW, DOMAIN, OUTLINE_DATA
from custom_components.sun_sweep.coordinator import SunSweepCoordinator
from custom_components.sun_sweep.sensor import SunSweepSensor
from custom_components.sun_sweep.sweep import project_outline, snapshot

LAT, LON = 53.5461, -113.4938


def _place(hass: HomeAssistant) -> None:
    hass.config.latitude = LAT
    hass.config.longitude = LON
    hass.config.time_zone = "America/Edmonton"


def _sensor(hass: HomeAssistant, when: datetime) -> SunSweepSensor:
    """The sensor as it would read at ``when``, without loading dependencies."""
    entry = MockConfigEntry(domain=DOMAIN, title="Sun Sweep", data={})
    entry.add_to_hass(hass)
    coordinator = SunSweepCoordinator(hass, entry)
    info = hass.data.get(OUTLINE_DATA) or {}
    points = [] if info.get("failed") else info.get("points") or []
    coordinator.data = snapshot(when, LAT, LON, points)
    coordinator.last_update_success = True
    sensor = SunSweepSensor(coordinator)
    sensor.hass = hass
    return sensor


def test_a_missing_outline_is_empty_and_does_not_raise(hass: HomeAssistant) -> None:
    _place(hass)
    when = datetime(2026, 6, 21, 9, 30, tzinfo=ZoneInfo("America/Edmonton"))
    sensor = _sensor(hass, when)
    assert sensor.native_value == ABOVE
    assert sensor.extra_state_attributes["outline"] == []
    assert sensor.extra_state_attributes["sun_clockwise"] is True


def test_the_outline_is_centred_metres(hass: HomeAssistant) -> None:
    _place(hass)
    per = 111_320.0
    cos = math.cos(math.radians(LAT))
    ring = [
        (LAT + north / per, LON + east / (per * cos))
        for north, east in ((-4, -6), (-4, 6), (4, 6), (4, -6))
    ]
    hass.data[OUTLINE_DATA] = {"points": ring, "rotation": 1.0}
    when = datetime(2026, 12, 21, 23, 0, tzinfo=ZoneInfo("America/Edmonton"))
    sensor = _sensor(hass, when)
    assert sensor.native_value == BELOW
    assert sensor.extra_state_attributes["outline"] == project_outline(ring)
    assert "points" not in str(sensor.extra_state_attributes["outline"])


def test_the_coordinator_draws_a_square_until_house_structure_is_installed(
    hass: HomeAssistant,
) -> None:
    _place(hass)
    entry = MockConfigEntry(domain=DOMAIN, title="Sun Sweep", data={})
    entry.add_to_hass(hass)
    coordinator = SunSweepCoordinator(hass, entry)
    when = datetime(2026, 6, 21, 9, 30, tzinfo=ZoneInfo("America/Edmonton"))
    fallback = coordinator._read(when, False)
    assert fallback["outline_fallback"] is True
    assert fallback["outline"][0] == [-5.0, -5.0]
    missing = coordinator._read(when, True)
    assert missing["outline"] == []
    assert "outline_fallback" not in missing


def test_a_failed_fetch_is_the_same_as_no_building(hass: HomeAssistant) -> None:
    _place(hass)
    hass.data[OUTLINE_DATA] = {"failed": True}
    when = datetime(2026, 6, 21, 9, 30, tzinfo=ZoneInfo("America/Edmonton"))
    sensor = _sensor(hass, when)
    assert sensor.extra_state_attributes["outline"] == []
