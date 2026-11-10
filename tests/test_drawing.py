# Copyright (c) 2026 MinchinWeb
"""The reference SVG: wedge, hours, house, sun and moon."""

from __future__ import annotations

import math
import re

import pytest

from custom_components.sun_sweep.drawing import card_svg, label_baseline, point_at

HOUSE = [[-5, -4], [5, -4], [5, 4], [-5, 4]]

SUMMER = {
    "sunrise": "2026-06-21T05:04:49-06:00",
    "sunset": "2026-06-21T22:06:53-06:00",
    "sun_azimuth": 98.2,
    "sun_elevation": 35.5,
    "moon_azimuth": 250.0,
    "moon_elevation": 20.0,
    "sunrise_azimuth": 46.5,
    "sunset_azimuth": 313.5,
    "hour_azimuths": [
        {"time": "06:00", "azimuth": 62.0},
        {"time": "09:00", "azimuth": 95.0},
    ],
    "outline": HOUSE,
    "pale_start": 46.5,
    "pale_end": 313.5,
    "pale_full": False,
    "strong_start": 46.5,
    "strong_end": 98.2,
    "strong_full": False,
}


def test_a_summer_morning_draws_the_elapsed_wedge_and_both_bodies():
    svg = card_svg(SUMMER)
    assert 'id="pale"' in svg and 'id="strong"' in svg
    assert "0 1 1" in svg  # the long summer arc, clockwise
    assert svg.count("<line ") == 2
    assert 'id="house"' in svg and 'id="sun"' in svg and 'id="moon"' in svg
    assert svg.count('fill-opacity="0.5"') == 2
    assert "5:04 AM" in svg and "10:06 PM" in svg
    assert svg.count('transform="rotate(') == 2
    assert ">N<" in svg
    assert 'id="ring"' in svg and 'stroke="#111111"' in svg
    assert 'id="ring-halo"' in svg and 'stroke="#ffffff"' in svg
    assert "<title>Where the sun travels today</title>" in svg
    assert "<title>Sunlight already past</title>" in svg
    assert 'paint-order="stroke"' in svg
    halo = svg.index('id="ring-halo"')
    ring = svg.index('id="ring"')
    assert svg.index('id="hours"') < halo < ring < svg.index('id="house"')
    end = point_at(313.5, 128)
    assert f"{end[0]:.1f}" in svg
    sun = point_at(SUMMER["sun_azimuth"], 128)
    moon = point_at(SUMMER["moon_azimuth"], 128)
    assert f'cx="{sun[0]:.1f}"' in svg
    assert f'cx="{moon[0]:.1f}"' in svg


def test_noon_reaches_the_centre_and_every_third_hour_runs_longer():
    marked = {
        **SUMMER,
        "hour_azimuths": [
            {"time": "12:00", "azimuth": 180.0},
            {"time": "15:00", "azimuth": 230.0},
            {"time": "16:00", "azimuth": 245.0},
        ],
    }
    svg = card_svg(marked)
    assert 'x1="160.0" y1="160.0"' in svg
    lines = re.findall(r"<line [^>]*>", svg)
    inners = []
    for line in lines:
        x1, y1 = re.search(r'x1="([\d.]+)" y1="([\d.]+)"', line).groups()
        inners.append(math.hypot(float(x1) - 160, float(y1) - 160))
        if x1 == "160.0" and y1 == "160.0":
            assert 'stroke-width="4"' in line
        else:
            assert 'stroke-width="1.5"' in line
    inners.sort()
    assert inners[0] == pytest.approx(0, abs=0.05)
    assert inners[1] < inners[2]


def test_a_short_winter_arc_is_the_minor_one():
    winter = {
        **SUMMER,
        "sunrise": "2026-12-21T09:48:00-07:00",
        "sunset": "2026-12-21T17:15:00-07:00",
        "sun_azimuth": 200.0,
        "sun_elevation": 8.0,
        "pale_start": 130.6,
        "pale_end": 229.4,
        "strong_start": 130.6,
        "strong_end": 200.0,
        "hour_azimuths": [{"time": "15:00", "azimuth": 200.0}],
    }
    svg = card_svg(winter)
    assert "A 128.0 128.0 0 0 1" in svg  # the short arc, clockwise
    assert "A 128.0 128.0 0 1 1" not in svg


def test_after_sunset_the_sun_marker_is_hidden_and_the_wedge_remains():
    night = {
        **SUMMER,
        "sun_elevation": -10.0,
        "strong_start": 46.5,
        "strong_end": 313.5,
    }
    svg = card_svg(night)
    assert 'id="strong"' in svg
    assert 'id="sun"' not in svg
    assert 'id="hours"' in svg
    assert "5:04 AM" in svg


def test_twilight_is_drawn_under_the_day_unless_turned_off():
    wider = {**SUMMER, "twilight_start": 20.0, "twilight_end": 340.0}
    svg = card_svg(wider)
    assert svg.index('id="twilight"') < svg.index('id="pale"')
    assert "<title>Civil twilight</title>" in svg
    hidden = card_svg(wider, {"show_twilight": False})
    assert 'id="twilight"' not in hidden
    assert 'id="pale"' in hidden


def test_toggles_drop_their_marks():
    svg = card_svg(
        SUMMER,
        {
            "show_sun": False,
            "show_moon": False,
            "show_hours": False,
            "show_times": False,
        },
    )
    assert 'id="sun"' not in svg
    assert 'id="moon"' not in svg
    assert 'id="hours"' not in svg
    assert "5:04 AM" not in svg
    assert 'id="pale"' in svg and 'id="house"' in svg


def test_times_sit_outside_the_wedge_on_the_spoke():
    svg = card_svg(SUMMER)
    assert 'dominant-baseline="middle"' not in svg
    for ident in ("sunrise", "sunset"):
        tag = re.search(rf'<text id="{ident}"[^>]*>', svg).group(0)
        assert 'text-anchor="middle"' in tag
        assert 'dominant-baseline="alphabetic"' in tag
    west_rise = card_svg({**SUMMER, "sunrise_azimuth": 200.0})
    rise = re.search(r'<text id="sunrise"[^>]*>', west_rise).group(0)
    assert 'dominant-baseline="text-before-edge"' in rise
    south = card_svg({**SUMMER, "sun_clockwise": False})
    assert south.count('dominant-baseline="text-before-edge"') == 2
    assert label_baseline(46.5, sunrise=True, sun_clockwise=True) == "alphabetic"
    assert label_baseline(313.5, sunrise=False, sun_clockwise=True) == "alphabetic"


def test_a_rotation_turns_the_whole_picture():
    svg = card_svg(SUMMER, {"rotation": -20})
    assert 'id="rotation"' in svg
    assert "rotate(-20.0 160.0 160.0)" in svg
    assert 'id="rotation"' not in card_svg(SUMMER)


def test_a_missing_outline_explains_itself():
    svg = card_svg({"outline": []})
    assert "no building outline" in svg
    assert 'id="house"' not in svg
