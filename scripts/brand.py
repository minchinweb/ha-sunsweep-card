# Copyright (c) 2026 MinchinWeb
"""Draw the Sun Sweep mark: a top-down house on its daylight wedge.

Writes the SVG sources under ``brand/`` and the PNG files Home Assistant
shows on the integration page. Sizes follow the integration brands guide:
a square icon at 256 and 512, and a landscape logo whose short side is 256
and 512. Run from the repository root::

    uv run python scripts/brand.py

Needs Pillow, which the test environment already has, and optipng on PATH
so the files are interlaced, which the brands guide prefers.
"""

from __future__ import annotations

import contextlib
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "brand" / "fonts" / "Figtree-Variable.ttf"
BRAND = ROOT / "custom_components" / "sun_sweep" / "brand"
SOURCES = ROOT / "brand"

# The day's whole arc stays faint so the swept part (sunrise to now) stands
# clear of it: over 2:1 on white and on a dark dashboard. The swept amber is
# deeper than the card's, which also sets the sun disc apart from it.
PALE_OPACITY = 0.3
PALE = (246, 216, 74, round(255 * PALE_OPACITY))
STRONG_HEX = "#d4900a"
STRONG = (212, 144, 10, 255)
SUN = (245, 196, 0, 255)
SUN_EDGE = (165, 107, 0, 255)
RING = (17, 17, 17, 255)
RING_HALO = (255, 255, 255, 255)
# On a dark dashboard a black ring vanishes, so the two swap.
DARK_RING = (244, 247, 251, 255)
DARK_RING_HALO = (17, 17, 17, 255)
# The sun is a sixth of the radius, plus a tenth so it holds up when small.
SUN_SIZE = 1 / 5.45

# A northern summer day: sunrise in the north-east, sun mid-morning, sunset north-west.
RISE, NOW, SET = 48.0, 108.0, 314.0


def _at(azimuth: float, radius: float, centre: float) -> tuple[float, float]:
    turn = math.radians(azimuth)
    return centre + radius * math.sin(turn), centre - radius * math.cos(turn)


def _sector(
    start: float, end: float, radius: float, centre: float
) -> list[tuple[float, float]]:
    span = (end - start) % 360.0
    steps = max(2, int(span / 3))
    points = [(centre, centre)]
    for step in range(steps + 1):
        points.append(_at(start + span * step / steps, radius, centre))
    return points


def _house(centre: float, rim: float) -> list[tuple[float, float]]:
    """An L-shaped plan, about 42% of the disc across."""
    scale = rim * 0.34
    # east, north
    corners = [
        (-1.0, -0.7),
        (1.0, -0.7),
        (1.0, 0.15),
        (0.1, 0.15),
        (0.1, 0.7),
        (-1.0, 0.7),
    ]
    return [(centre + east * scale, centre - north * scale) for east, north in corners]


def _offset(
    points: list[tuple[float, float]], distance: float
) -> list[tuple[float, float]]:
    """Mitre a plan out by ``distance`` (in by when negative).

    Every corner of the plan is a right angle, so each moves along the
    diagonal between its two edge normals.
    """
    count = len(points)
    area = sum(
        points[i][0] * points[(i + 1) % count][1]
        - points[(i + 1) % count][0] * points[i][1]
        for i in range(count)
    )
    # Screen y points down, so a positive sum winds clockwise on screen.
    side = 1.0 if area > 0 else -1.0
    moved = []
    for i, (x, y) in enumerate(points):
        before = points[i - 1]
        after = points[(i + 1) % count]
        shift_x = shift_y = 0.0
        for start, end in ((before, (x, y)), ((x, y), after)):
            run_x, run_y = end[0] - start[0], end[1] - start[1]
            length = math.hypot(run_x, run_y)
            # Outward normal of a clockwise edge on screen is (dy, -dx).
            shift_x += side * run_y / length
            shift_y += -side * run_x / length
        moved.append((x + shift_x * distance, y + shift_y * distance))
    return moved


def _weights(rim: float) -> tuple[int, int, int]:
    """Ring, a slim light edge, and a house stroke heavier than the ring.

    The mark is shown at a few dozen pixels, so the strokes are a larger
    share of the disc than on the card.
    """
    ring = max(3, round(rim / 8))
    halo = ring + max(4, round(rim / 40))
    house = max(ring, round(rim / 6))
    return ring, halo, house


def draw_mark(image: Image.Image, centre: float, rim: float, dark: bool) -> None:
    """The wedge, the ring, the house and the sun, centred in ``image``."""
    draw = ImageDraw.Draw(image, "RGBA")
    draw.polygon(_sector(RISE, SET, rim, centre), fill=PALE)
    draw.polygon(_sector(RISE, NOW, rim, centre), fill=STRONG)
    ring, halo, house_width = _weights(rim)
    # Pillow draws an outline inward from its box, but the ring is centred on
    # the radius (as in the SVG), which is where the sun rides.
    for width, colour in (
        (halo, DARK_RING_HALO if dark else RING_HALO),
        (ring, DARK_RING if dark else RING),
    ):
        reach = rim + width / 2
        draw.ellipse(
            (centre - reach, centre - reach, centre + reach, centre + reach),
            outline=colour,
            width=width,
        )
    house = _house(centre, rim)
    fill = (36, 48, 64, 255) if dark else (247, 244, 239, 255)
    edge = (244, 247, 251, 255) if dark else (61, 74, 87, 255)
    # Square corners: the wall is a mitred band half a stroke either side of
    # the plan, so every corner is a hard right angle, the closing one too.
    draw.polygon(_offset(house, house_width / 2), fill=edge)
    draw.polygon(_offset(house, -house_width / 2), fill=fill)
    sun = _at(NOW, rim, centre)
    radius = max(6, round(rim * SUN_SIZE))
    draw.ellipse(
        (sun[0] - radius, sun[1] - radius, sun[0] + radius, sun[1] + radius),
        fill=SUN,
        outline=SUN_EDGE,
        width=max(2, ring // 3),
    )


def _font(size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT), size)
    with contextlib.suppress(OSError, AttributeError):
        font.set_variation_by_axes([600])
    return font


def _tight_mark(dark: bool) -> Image.Image:
    """The mark, cropped to its pixels, drawn large enough to scale cleanly."""
    big = 2048
    work = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw_mark(work, big / 2, big * 0.36, dark)
    box = work.getbbox()
    if box is None:
        return work
    return work.crop(box)


def _icon(pixels: int, dark: bool) -> Image.Image:
    """A square icon. The mark fills it; only the shorter axis is letterboxed."""
    mark = _tight_mark(dark)
    side = max(mark.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.alpha_composite(mark, ((side - mark.width) // 2, (side - mark.height) // 2))
    return square.resize((pixels, pixels), Image.Resampling.LANCZOS)


def _logo(height: int, dark: bool) -> Image.Image:
    """A landscape wordmark whose short side is ``height``, with no outer margin."""
    mark = _icon(height, dark)
    # The old wordmark was sized against a padded mark. Keep that proportion
    # now that the mark fills its square (the wedge used 0.72 of the canvas).
    font = _font(round(height * 0.42 / 0.72))
    text = "Sun Sweep"
    gap = round(height * 0.12)
    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    width = math.ceil(measure.textlength(text, font=font))
    image = Image.new("RGBA", (height + gap + width, height), (0, 0, 0, 0))
    image.alpha_composite(mark, (0, 0))
    ink = (244, 247, 251, 255) if dark else (61, 74, 87, 255)
    draw = ImageDraw.Draw(image)
    draw.text((height + gap, height / 2), text, font=font, fill=ink, anchor="lm")
    box = image.getbbox()
    if box is None:
        return image
    cropped = image.crop(box)
    short = min(cropped.size)
    if short == height:
        return cropped
    factor = height / short
    return cropped.resize(
        (round(cropped.width * factor), round(cropped.height * factor)),
        Image.Resampling.LANCZOS,
    )


def _save(image: Image.Image, path: Path) -> None:
    image.save(path, format="PNG", optimize=True)
    optipng = shutil.which("optipng")
    if optipng is None:
        raise SystemExit("optipng is required to write interlaced brand images")
    subprocess.run([optipng, "-i", "1", "-o", "2", "-quiet", str(path)], check=True)


def _svg(dark: bool) -> str:
    """The icon as SVG, cropped to the mark the same way as the PNG."""
    edge = "#f4f7fb" if dark else "#3d4a57"
    fill = "#243040" if dark else "#f7f4ef"
    centre, rim = 256.0, 184.0
    sun = _at(NOW, rim, centre)
    ring, halo, house_width = _weights(rim)
    sun_r = max(6, round(rim * SUN_SIZE))
    ring_colour = "#f4f7fb" if dark else "#111111"
    halo_colour = "#111111" if dark else "#ffffff"
    outer = rim + halo / 2
    points = [
        *_sector(RISE, SET, rim, centre),
        *_house(centre, rim),
        (centre - outer, centre),
        (centre + outer, centre),
        (centre, centre - outer),
        (centre, centre + outer),
        (sun[0] - sun_r, sun[1]),
        (sun[0] + sun_r, sun[1]),
        (sun[0], sun[1] - sun_r),
        (sun[0], sun[1] + sun_r),
    ]
    pad = 4.0
    left = min(point[0] for point in points) - pad
    top = min(point[1] for point in points) - pad
    right = max(point[0] for point in points) + pad
    bottom = max(point[1] for point in points) + pad

    def sector(start: float, end: float) -> str:
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in _sector(start, end, rim, centre))

    house = " ".join(f"{x:.1f},{y:.1f}" for x, y in _house(centre, rim))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left:.1f} {top:.1f} '
        f'{right - left:.1f} {bottom - top:.1f}">'
        f'<polygon points="{sector(RISE, SET)}" fill="#f6d84a" '
        f'fill-opacity="{PALE_OPACITY}"/>'
        f'<polygon points="{sector(RISE, NOW)}" fill="{STRONG_HEX}" '
        f'fill-opacity="1"/>'
        f'<circle cx="{centre:.1f}" cy="{centre:.1f}" r="{rim:.1f}" fill="none" '
        f'stroke="{halo_colour}" stroke-width="{halo}"/>'
        f'<circle cx="{centre:.1f}" cy="{centre:.1f}" r="{rim:.1f}" fill="none" '
        f'stroke="{ring_colour}" stroke-width="{ring}"/>'
        f'<polygon points="{house}" fill="{fill}" stroke="{edge}" '
        f'stroke-linejoin="miter" '
        f'stroke-width="{house_width}"/>'
        f'<circle cx="{sun[0]:.1f}" cy="{sun[1]:.1f}" r="{sun_r}" fill="#f5c400" '
        f'stroke="#a56b00" stroke-width="6"/></svg>\n'
    )


def main() -> None:
    SOURCES.mkdir(parents=True, exist_ok=True)
    BRAND.mkdir(parents=True, exist_ok=True)
    (SOURCES / "icon.svg").write_text(_svg(False), encoding="utf-8")
    (SOURCES / "dark_icon.svg").write_text(_svg(True), encoding="utf-8")
    for dark, name in ((False, "icon"), (True, "dark_icon")):
        _save(_icon(256, dark), BRAND / f"{name}.png")
        _save(_icon(512, dark), BRAND / f"{name}@2x.png")
    for dark, name in ((False, "logo"), (True, "dark_logo")):
        logo = _logo(256, dark)
        _save(logo, BRAND / f"{name}.png")
        _save(_logo(512, dark), BRAND / f"{name}@2x.png")
        _save(logo, SOURCES / f"{name}.png")


if __name__ == "__main__":
    main()
