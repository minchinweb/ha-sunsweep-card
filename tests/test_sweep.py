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
    finish_snapshot,
    moon_position,
    project_outline,
    resolve_when,
    snapshot,
    travel,
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


def test_twilight_reaches_beyond_sunrise_and_sunset():
    sweep = day_sweep(_at(EDMONTON, 2026, 6, 21, 9, 30), LAT, LON)
    assert sweep.twilight is not None and sweep.pale is not None
    dawn, dusk, _ = sweep.twilight
    rise, sett, _ = sweep.pale
    assert travel(dawn, rise, True) > 0
    assert travel(dawn, sett, True) < travel(dawn, dusk, True)
    assert "twilight_start" in sweep.attributes()


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
    assert sweep.twilight is None


def test_polar_night_has_no_sector_and_no_hour_lines():
    sweep = day_sweep(_at(POLAR, 2026, 12, 21, 12), 78.22, 15.63)
    assert sweep.phase == "polar_night"
    assert sweep.pale is None
    assert sweep.strong is None
    assert sweep.hours == ()
    assert sweep.sun_elevation < 0
    assert sweep.twilight is None


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


def test_a_bare_date_keeps_the_clock_time_and_a_full_one_replaces_it():
    now = _at(EDMONTON, 2026, 6, 21, 9, 30)
    assert resolve_when(now, "2026-12-21", None) == _at(EDMONTON, 2026, 12, 21, 9, 30)
    assert resolve_when(now, "2026-12-21", "15:04") == _at(
        EDMONTON, 2026, 12, 21, 15, 4
    )
    pinned = resolve_when(now, "2026-01-02T08:15:00-07:00", None)
    assert pinned == datetime(2026, 1, 2, 8, 15, tzinfo=EDMONTON)
    with pytest.raises(ValueError):
        resolve_when(now, "June", None)


def test_an_equinox_is_that_day_in_the_home_year():
    now = _at(EDMONTON, 2026, 6, 21, 9, 30)
    march = resolve_when(now, "march-equinox", "12:00")
    september = resolve_when(now, "september equinox", None)
    assert (march.month, march.day, march.hour) == (3, 20, 12)
    assert (september.month, september.day) == (9, 22)
    assert (september.hour, september.minute) == (9, 30)


def test_a_solstice_is_that_day_in_the_home_year():
    now = _at(EDMONTON, 2026, 6, 21, 9, 30)
    june = resolve_when(now, "june-solstice", "12:00", LAT)
    december = resolve_when(now, "winter solstice", None, LAT)
    assert (june.month, june.day, june.hour) == (6, 21, 12)
    assert (december.month, december.day) == (12, 21)
    assert (december.hour, december.minute) == (9, 30)


def test_season_names_follow_the_hemisphere():
    now = _at(EDMONTON, 2026, 6, 21, 9, 30)
    south = -33.9
    assert resolve_when(now, "summer-solstice", "12:00", south).month == 12
    assert resolve_when(now, "winter-solstice", "12:00", south).month == 6
    assert resolve_when(now, "spring-equinox", "12:00", south).month == 9
    assert resolve_when(now, "autumn-equinox", "12:00", south).month == 3
    assert resolve_when(now, "march-equinox", "12:00", south).month == 3
    assert resolve_when(now, "june-solstice", "12:00", south).month == 6
    assert resolve_when(now, "summer", "12:00", south).month == 12
    assert resolve_when(now, "winter", "12:00", south).month == 6
    assert resolve_when(now, "spring", "12:00", south).month == 9
    assert resolve_when(now, "autumn", "12:00", south).month == 3
    assert resolve_when(now, "summer", "12:00", LAT).month == 6
    assert resolve_when(now, "winter", "12:00", LAT).month == 12


def test_without_house_structure_the_outline_is_a_ten_metre_square():
    when = _at(EDMONTON, 2026, 6, 21, 9, 30)
    attrs = finish_snapshot(when, LAT, LON, None, house_structure=False)
    assert attrs["outline_fallback"] is True
    assert attrs["outline"] == [[-5.0, -5.0], [5.0, -5.0], [5.0, 5.0], [-5.0, 5.0]]
    ring = [(LAT, LON), (LAT, LON + 0.001), (LAT + 0.001, LON)]
    kept = finish_snapshot(when, LAT, LON, ring, house_structure=True)
    assert "outline_fallback" not in kept
    assert kept["outline"]


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
