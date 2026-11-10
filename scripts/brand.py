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

PALE = (246, 216, 74, 90)
STRONG = (240, 180, 41, 184)
SUN = (245, 196, 0, 255)
SUN_EDGE = (165, 107, 0, 255)
RING = (17, 17, 17, 255)
RING_HALO = (255, 255, 255, 255)

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
    disc = (centre - rim, centre - rim, centre + rim, centre + rim)
    draw.ellipse(disc, outline=RING_HALO, width=halo)
    draw.ellipse(disc, outline=RING, width=ring)
    house = _house(centre, rim)
    fill = (36, 48, 64, 255) if dark else (247, 244, 239, 255)
    edge = (244, 247, 251, 255) if dark else (61, 74, 87, 255)
    draw.polygon(house, fill=fill)
    draw.line([*house, house[0]], fill=edge, width=house_width, joint="curve")
    sun = _at(NOW, rim, centre)
    radius = max(4, int(rim / 11))
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
    outer = rim + halo / 2
    points = [
        *_sector(RISE, SET, rim, centre),
        *_house(centre, rim),
        (centre - outer, centre),
        (centre + outer, centre),
        (centre, centre - outer),
        (centre, centre + outer),
        (sun[0] - 24, sun[1]),
        (sun[0] + 24, sun[1]),
        (sun[0], sun[1] - 24),
        (sun[0], sun[1] + 24),
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
        f'<polygon points="{sector(RISE, SET)}" fill="#f6d84a" fill-opacity="0.35"/>'
        f'<polygon points="{sector(RISE, NOW)}" fill="#f0b429" fill-opacity="0.72"/>'
        f'<circle cx="{centre:.1f}" cy="{centre:.1f}" r="{rim:.1f}" fill="none" '
        f'stroke="#ffffff" stroke-width="{halo}"/>'
        f'<circle cx="{centre:.1f}" cy="{centre:.1f}" r="{rim:.1f}" fill="none" '
        f'stroke="#111111" stroke-width="{ring}"/>'
        f'<polygon points="{house}" fill="{fill}" stroke="{edge}" '
        f'stroke-width="{house_width}"/>'
        f'<circle cx="{sun[0]:.1f}" cy="{sun[1]:.1f}" r="18" fill="#f5c400" '
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
