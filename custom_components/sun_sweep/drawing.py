# Copyright (c) 2026 MinchinWeb
"""The top-down card: house over today's sun wedge.

This is the reference drawing. The Lovelace card
(``frontend/sun-sweep-card.js``) draws the same shapes from the same sensor
attributes. North is up. An azimuth maps to the disc with
``x = cx + r * sin(azimuth)``, ``y = cy - r * cos(azimuth)``.
"""

from __future__ import annotations

from datetime import datetime
import math

from .constants import (
    HOUR,
    HOUSE_FILL,
    HOUSE_STROKE,
    MOON_FILL,
    MOON_STROKE,
    PALE,
    PALE_OPACITY,
    STRONG,
    STRONG_OPACITY,
    SUN_FILL,
    SUN_STROKE,
)
from .sweep import travel

SIZE = 320
_RIM = 112.0
_MOON_RIM = 128.0
_SUN_R = 7.0
_MOON_R = 6.0


def point_at(azimuth: float, radius: float, size: int = SIZE) -> tuple[float, float]:
    """A point on the disc. Azimuth is degrees clockwise from north."""
    mid = size / 2
    turn = math.radians(azimuth)
    return mid + radius * math.sin(turn), mid - radius * math.cos(turn)


def card_svg(attrs: dict, options: dict | None = None, size: int = SIZE) -> str:
    """The card as an SVG document.

    Args:
        attrs: The sensor attributes (``outline``, the wedge, the bodies).
        options: ``show_sun``, ``show_times``, ``show_moon``, ``show_hours``.
            Each defaults on.
        size: Width and height in pixels.

    Returns:
        An SVG string. With no outline, a one-line explanation and no disc.
    """
    flags = _flags(options)
    if not attrs.get("outline"):
        return _message(
            size, "House Structure has no building outline for this home yet."
        )
    parts = _parts(attrs, flags, size)
    body = "".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" font-family="sans-serif" font-size="13">'
        f"{body}</svg>"
    )


def _flags(options: dict | None) -> dict[str, bool]:
    options = options or {}
    return {
        key: options.get(key) is not False
        for key in ("show_sun", "show_times", "show_moon", "show_hours")
    }


def _message(size: int, text: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" font-family="sans-serif" font-size="14">'
        f'<text x="{size / 2}" y="{size / 2}" text-anchor="middle" '
        f'fill="var(--primary-text-color)">{text}</text></svg>'
    )


def _parts(attrs: dict, flags: dict[str, bool], size: int) -> list[str]:
    """Draw order: pale wedge, strong wedge, rim, hours, house, sun, moon, times, N."""
    parts: list[str] = []
    rim = _RIM * size / SIZE
    sun_clockwise = attrs.get("sun_clockwise", True)
    if attrs.get("pale_full"):
        parts.append(
            f'<circle id="pale" cx="{size / 2}" cy="{size / 2}" r="{rim:.1f}" '
            f'fill="{PALE}" fill-opacity="{PALE_OPACITY}"/>'
        )
        parts.append(
            f'<circle id="rim" cx="{size / 2}" cy="{size / 2}" r="{rim:.1f}" '
            f'fill="none" stroke="{HOUR}" stroke-width="1.5"/>'
        )
    elif attrs.get("pale_start") is not None:
        parts.append(
            _wedge(
                "pale",
                attrs["pale_start"],
                attrs["pale_end"],
                rim,
                PALE,
                PALE_OPACITY,
                size,
                sun_clockwise,
            )
        )
        parts.append(
            _arc(
                "rim", attrs["pale_start"], attrs["pale_end"], rim, size, sun_clockwise
            )
        )
    if attrs.get("strong_full"):
        parts.append(
            f'<circle id="strong" cx="{size / 2}" cy="{size / 2}" r="{rim:.1f}" '
            f'fill="{STRONG}" fill-opacity="{STRONG_OPACITY}"/>'
        )
    elif attrs.get("strong_start") is not None:
        parts.append(
            _wedge(
                "strong",
                attrs["strong_start"],
                attrs["strong_end"],
                rim,
                STRONG,
                STRONG_OPACITY,
                size,
                sun_clockwise,
            )
        )
    house = _house(attrs["outline"], size, rim)
    if flags["show_hours"] and attrs.get("hour_azimuths"):
        inner = min(house[1] + 6, rim - 8)
        lines = []
        for mark in attrs["hour_azimuths"]:
            x1, y1 = point_at(mark["azimuth"], inner, size)
            x2, y2 = point_at(mark["azimuth"], rim, size)
            lines.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{HOUR}" stroke-width="1.5"/>'
            )
        parts.append(f'<g id="hours">{"".join(lines)}</g>')
    parts.append(house[0])
    if flags["show_sun"] and attrs.get("sun_elevation", -1) > 0:
        x, y = point_at(attrs["sun_azimuth"], rim, size)
        parts.append(
            f'<circle id="sun" cx="{x:.1f}" cy="{y:.1f}" r="{_SUN_R}" '
            f'fill="{SUN_FILL}" stroke="{SUN_STROKE}" stroke-width="1.5"/>'
        )
    if flags["show_moon"] and attrs.get("moon_elevation", -1) > 0:
        x, y = point_at(attrs["moon_azimuth"], _MOON_RIM * size / SIZE, size)
        parts.append(
            f'<circle id="moon" cx="{x:.1f}" cy="{y:.1f}" r="{_MOON_R}" '
            f'fill="{MOON_FILL}" stroke="{MOON_STROKE}" stroke-width="1.5"/>'
        )
    if flags["show_times"]:
        parts.extend(_times(attrs, size, rim))
    nx, ny = point_at(0, rim + 14, size)
    parts.append(
        f'<text id="north" x="{nx:.1f}" y="{ny + 4:.1f}" text-anchor="middle" '
        f'fill="var(--primary-text-color)">N</text>'
    )
    return parts


def _wedge(name, start, end, radius, fill, opacity, size, sun_clockwise) -> str:
    span = travel(start, end, sun_clockwise)
    x1, y1 = point_at(start, radius, size)
    x2, y2 = point_at(end, radius, size)
    large = 1 if span > 180 else 0
    sweep = 1 if sun_clockwise else 0
    mid = size / 2
    return (
        f'<path id="{name}" d="M {mid:.1f} {mid:.1f} L {x1:.1f} {y1:.1f} '
        f'A {radius:.1f} {radius:.1f} 0 {large} {sweep} {x2:.1f} {y2:.1f} Z" '
        f'fill="{fill}" fill-opacity="{opacity}"/>'
    )


def _arc(name, start, end, radius, size, sun_clockwise) -> str:
    span = travel(start, end, sun_clockwise)
    x1, y1 = point_at(start, radius, size)
    x2, y2 = point_at(end, radius, size)
    large = 1 if span > 180 else 0
    sweep = 1 if sun_clockwise else 0
    return (
        f'<path id="{name}" d="M {x1:.1f} {y1:.1f} '
        f'A {radius:.1f} {radius:.1f} 0 {large} {sweep} {x2:.1f} {y2:.1f}" '
        f'fill="none" stroke="{HOUR}" stroke-width="1.5"/>'
    )


def _house(outline: list, size: int, rim: float) -> tuple[str, float]:
    """The polygon, and the radius of the furthest corner from the centre."""
    easts = [p[0] for p in outline]
    norths = [p[1] for p in outline]
    span = max(max(easts) - min(easts), max(norths) - min(norths), 1e-6)
    scale = 0.42 * 2 * rim / span
    mid = size / 2
    pts = [(mid + e * scale, mid - n * scale) for e, n in outline]
    radius = max(math.hypot(x - mid, y - mid) for x, y in pts)
    polygon = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (
        f'<polygon id="house" points="{polygon}" fill="{HOUSE_FILL}" '
        f'stroke="{HOUSE_STROKE}" stroke-width="2"/>'
    ), radius


def _times(attrs: dict, size: int, rim: float) -> list[str]:
    labels = []
    for key, az_key, ident in (
        ("sunrise", "sunrise_azimuth", "sunrise"),
        ("sunset", "sunset_azimuth", "sunset"),
    ):
        if not attrs.get(key) or attrs.get(az_key) is None:
            continue
        text = _clock(attrs[key])
        x, y = _label_at(attrs[az_key], size, rim)
        labels.append(
            f'<text id="{ident}" x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
            f'dominant-baseline="middle" fill="var(--primary-text-color)">{text}</text>'
        )
    return labels


def _clock(iso: str) -> str:
    """A 12-hour clock time, for the reference pictures."""
    moment = datetime.fromisoformat(iso)
    text = moment.strftime("%I:%M %p")
    return text.removeprefix("0")


def _label_at(azimuth: float, size: int, rim: float) -> tuple[float, float]:
    """Just outside the rim, pulled inward when the words would leave the box."""
    for radius in (rim + 16, rim - 20):
        x, y = point_at(azimuth, radius, size)
        if 40 <= x <= size - 40 and 12 <= y <= size - 8:
            return x, y
    return point_at(azimuth, rim - 20, size)
