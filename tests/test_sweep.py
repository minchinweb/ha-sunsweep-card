# Copyright (c) 2026 MinchinWeb
"""The daylight sector, the hour lines and the outline, without Home Assistant."""

from __future__ import annotations

from datetime import datetime
import math
from zoneinfo import ZoneInfo

import pytest

from custom_components.sun_sweep.sweep import (
    AFTER,
    BEFORE,
    DAY,
    _horizontal,
    clockwise,
    day_sweep,
    moon_position,
    project_outline,
    snapshot,
)

EDMONTON = ZoneInfo("America/Edmonton")
SYDNEY = ZoneInfo("Australia/Sydney")
POLAR = ZoneInfo("Arctic/Longyearbyen")
LAT, LON = 53.5461, -113.4938


def _at(zone, year, month, day, hour, minute=0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=zone)


def test_the_strong_sector_follows_the_sun_from_sunrise():
    morning = day_sweep(_at(EDMONTON, 2026, 6, 21, 9, 30), LAT, LON)
    assert morning.phase == DAY
    assert morning.sun_clockwise
    assert morning.strong is not None and morning.pale is not None
    rise, now, _ = morning.strong
    end = morning.pale[1]
    assert 0 < clockwise(rise, now) < clockwise(rise, end)


def test_the_southern_sun_travels_the_other_way_through_north():
    sweep = day_sweep(_at(SYDNEY, 2026, 1, 15, 10), -33.8688, 151.2093)
    assert sweep.phase == DAY
    assert sweep.sun_clockwise is False
    rise, now, _ = sweep.strong
    end = sweep.pale[1]
    # decreasing azimuth: already travelled is clockwise from now back to sunrise
    assert 0 < clockwise(now, rise) < clockwise(end, rise)


def test_before_sunrise_has_no_strong_wedge_and_no_sun():
    sweep = day_sweep(_at(EDMONTON, 2026, 6, 21, 3), LAT, LON)
    assert sweep.phase == BEFORE
    assert sweep.strong is None
    assert sweep.pale is not None
    assert sweep.sun_elevation < 0


def test_after_sunset_the_whole_sector_is_strong_and_the_sun_is_down():
    sweep = day_sweep(_at(EDMONTON, 2026, 6, 21, 23), LAT, LON)
    assert sweep.phase == AFTER
    assert sweep.strong == sweep.pale
    assert sweep.sun_elevation < 0


def test_hour_lines_lie_inside_the_sector_and_only_while_the_sun_is_up():
    sweep = day_sweep(_at(EDMONTON, 2026, 12, 21, 15), LAT, LON)
    rise, sett, _ = sweep.pale
    assert sweep.hours
    for moment, place in sweep.hours:
        assert clockwise(rise, place) <= clockwise(rise, sett) + 0.5
        assert moment.minute == 0
    # 15:00 is inside a winter afternoon; 08:00 is still night
    times = {moment.hour for moment, _ in sweep.hours}
    assert 15 in times
    assert 8 not in times


def test_polar_day_is_a_full_disc_with_hour_lines():
    sweep = day_sweep(_at(POLAR, 2026, 6, 21, 12), 78.22, 15.63)
    assert sweep.phase == "polar_day"
    assert sweep.pale == (0.0, 360.0, True)
    assert sweep.strong is not None
    assert len(sweep.hours) == 24
    assert sweep.sun_elevation > 0


def test_polar_night_has_no_sector_and_no_hour_lines():
    sweep = day_sweep(_at(POLAR, 2026, 12, 21, 12), 78.22, 15.63)
    assert sweep.phase == "polar_night"
    assert sweep.pale is None
    assert sweep.strong is None
    assert sweep.hours == ()
    assert sweep.sun_elevation < 0


def test_projection_centres_the_box_and_keeps_north_positive():
    per = 111_320.0
    lat, lon = LAT, LON
    cos = math.cos(math.radians(lat))
    ring = []
    for north, east in ((-4, -6), (-4, 6), (4, 6), (4, -6), (-4, -6)):
        ring.append((lat + north / per, lon + east / (per * cos)))
    projected = project_outline(ring)
    assert len(projected) == 4  # the repeated closing corner is dropped
    easts = [p[0] for p in projected]
    norths = [p[1] for p in projected]
    assert (min(easts) + max(easts)) / 2 == pytest.approx(0, abs=0.05)
    assert (min(norths) + max(norths)) / 2 == pytest.approx(0, abs=0.05)
    assert max(norths) == pytest.approx(4, abs=0.05)
    assert max(norths) > 0


def test_a_missing_outline_is_an_empty_list():
    attrs = snapshot(_at(EDMONTON, 2026, 6, 21, 9, 30), LAT, LON, None)
    assert attrs["outline"] == []
    assert attrs["sun_azimuth"] > 0


def test_an_object_due_east_on_the_equator_sits_on_the_horizon():
    azimuth, elevation = _horizontal(0.0, -math.pi / 2, 0.0)
    assert azimuth == pytest.approx(90, abs=0.01)
    assert elevation == pytest.approx(0, abs=0.01)


def test_the_moon_is_a_direction_on_the_sky():
    azimuth, elevation = moon_position(_at(EDMONTON, 2026, 6, 21, 9, 30), LAT, LON)
    assert 0 <= azimuth < 360
    assert -90 <= elevation <= 90
