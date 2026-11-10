# Copyright (c) 2026 MinchinWeb
"""Render the three README pictures from the card's drawing.

Run from the repository root::

    uv run python scripts/render_card.py

Each picture is the reference SVG (with the theme colour filled in for the
words) and a PNG of the same geometry.
"""

from __future__ import annotations

import contextlib
from datetime import datetime
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from custom_components.sun_sweep.drawing import card_svg, point_at
from custom_components.sun_sweep.sweep import snapshot, travel

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"
FONT = ROOT / "brand" / "fonts" / "Figtree-Variable.ttf"
ZONE = ZoneInfo("America/Edmonton")
LAT, LON = 53.5461, -113.4938
# a 12 m by 8 m plan, already centred
HOUSE = [[-6, -4], [6, -4], [6, 4], [-6, 4]]
INK = (61, 74, 87, 255)
PALE = (246, 216, 74, 90)
STRONG = (240, 180, 41, 184)
HOUR = (196, 138, 18, 255)
RING = (17, 17, 17, 255)
SUN = (245, 196, 0, 255)
MOON = (197, 208, 220, 255)
HOUSE_FILL = (247, 244, 239, 255)
HOUSE_EDGE = (61, 74, 87, 255)

SCENES = (
    ("summer-morning", datetime(2026, 6, 6, 9, 30, tzinfo=ZONE)),
    ("winter-afternoon", datetime(2026, 12, 21, 15, 0, tzinfo=ZONE)),
    ("after-sunset", datetime(2026, 6, 21, 23, 0, tzinfo=ZONE)),
)


def _sector(start, end, radius, size, sun_clockwise) -> list[tuple[float, float]]:
    span = travel(start, end, sun_clockwise)
    steps = max(2, int(span / 2))
    mid = size / 2
    points = [(mid, mid)]
    for step in range(steps + 1):
        azimuth = start + (span if sun_clockwise else -span) * step / steps
        points.append(point_at(azimuth, radius, size))
    return points


def _house(outline, size, rim) -> tuple[list[tuple[float, float]], float]:
    easts = [p[0] for p in outline]
    norths = [p[1] for p in outline]
    span = max(max(easts) - min(easts), max(norths) - min(norths), 1e-6)
    scale = 0.42 * 2 * rim / span
    mid = size / 2
    points = [(mid + east * scale, mid - north * scale) for east, north in outline]
    radius = max(math.hypot(x - mid, y - mid) for x, y in points)
    return points, radius


def _disc(image: Image.Image, x: float, y: float, radius: float, fill) -> None:
    """Full colour, then the right half washed white, matching the SVG disc."""
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)
    wash = Image.new("RGBA", image.size, (0, 0, 0, 0))
    # Pillow measures pieslice angles clockwise from 3 o'clock.
    # 270° to 90° is the right-hand semicircle.
    ImageDraw.Draw(wash).pieslice(
        (x - radius, y - radius, x + radius, y + radius),
        270,
        90,
        fill=(255, 255, 255, 128),
    )
    image.alpha_composite(wash)


def _label(azimuth, size, rim) -> tuple[float, float]:
    for radius in (rim + 16 * size / 320, rim - 20 * size / 320):
        x, y = point_at(azimuth, radius, size)
        if 40 * size / 320 <= x <= size - 40 * size / 320 and 12 <= y <= size - 8:
            return x, y
    return point_at(azimuth, rim - 20 * size / 320, size)


def _clock(iso: str) -> str:
    text = datetime.fromisoformat(iso).strftime("%I:%M %p")
    return text.removeprefix("0")


def paint(attrs: dict, size: int = 640) -> Image.Image:
    """A PNG of the card drawing, on white."""
    image = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    rim = 112.0 * size / 320
    sun_clockwise = attrs.get("sun_clockwise", True)
    if attrs.get("pale_full"):
        mid = size / 2
        draw.ellipse((mid - rim, mid - rim, mid + rim, mid + rim), fill=PALE)
    elif attrs.get("pale_start") is not None:
        draw.polygon(
            _sector(attrs["pale_start"], attrs["pale_end"], rim, size, sun_clockwise),
            fill=PALE,
        )
    ring = 128.0 * size / 320
    mid = size / 2
    draw.ellipse(
        (mid - ring, mid - ring, mid + ring, mid + ring),
        outline=RING,
        width=max(3, round(3 * size / 320)),
    )
    if attrs.get("strong_full"):
        mid = size / 2
        draw.ellipse((mid - rim, mid - rim, mid + rim, mid + rim), fill=STRONG)
    elif attrs.get("strong_start") is not None:
        draw.polygon(
            _sector(
                attrs["strong_start"], attrs["strong_end"], rim, size, sun_clockwise
            ),
            fill=STRONG,
        )
    house, house_radius = _house(attrs["outline"], size, rim)
    width = max(2, int(size / 160))
    draw.polygon(house, fill=HOUSE_FILL, outline=HOUSE_EDGE)
    draw.line([*house, house[0]], fill=HOUSE_EDGE, width=width)
    if attrs.get("hour_azimuths"):
        width = max(2, int(size / 220))
        for mark in attrs["hour_azimuths"]:
            hour = int(str(mark["time"])[:2])
            if hour == 12:
                inner = 0.0
            elif hour % 3 == 0:
                inner = house_radius * 0.45
            else:
                inner = min(house_radius + 6 * size / 320, rim - 8 * size / 320)
            draw.line(
                [
                    point_at(mark["azimuth"], inner, size),
                    point_at(mark["azimuth"], rim, size),
                ],
                fill=HOUR,
                width=width,
            )
    if attrs.get("sun_elevation", -1) > 0:
        x, y = point_at(attrs["sun_azimuth"], ring, size)
        _disc(image, x, y, 8 * size / 320, SUN)
    if attrs.get("moon_elevation", -1) > 0:
        x, y = point_at(attrs["moon_azimuth"], ring, size)
        _disc(image, x, y, 7 * size / 320, MOON)
    font = ImageFont.truetype(str(FONT), int(13 * size / 320))
    with contextlib.suppress(OSError, AttributeError):
        font.set_variation_by_axes([600])
    pairs = (("sunrise", "sunrise_azimuth"), ("sunset", "sunset_azimuth"))
    for key, azimuth_key in pairs:
        if not attrs.get(key) or attrs.get(azimuth_key) is None:
            continue
        x, y = _label(attrs[azimuth_key], size, rim)
        draw.text((x, y), _clock(attrs[key]), font=font, fill=INK, anchor="mm")
    nx, ny = point_at(0, ring - 18 * size / 320, size)
    draw.text((nx, ny + 4 * size / 320), "N", font=font, fill=INK, anchor="mm")
    return image


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, when in SCENES:
        attrs = snapshot(when, LAT, LON, HOUSE)
        svg = card_svg(attrs).replace("var(--primary-text-color)", "#3d4a57")
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        paint(attrs).save(OUT / f"{name}.png")
        print(
            name,
            attrs["phase"],
            "sun",
            attrs["sun_elevation"],
            "moon",
            attrs["moon_elevation"],
        )


if __name__ == "__main__":
    main()
