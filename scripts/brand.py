# Copyright (c) 2026 MinchinWeb
"""Draw the Sun Sweep mark: a top-down house on its daylight wedge.

The SVG files under ``brand/`` are the masters. The PNG files Home Assistant
shows on the integration page are rendered from them. Sizes follow the
integration brands guide: a square icon at 256 and 512, and a landscape logo
whose short side is 256 and 512. Run from the repository root::

    uv run --with fonttools python scripts/brand.py

fontTools outlines the wordmark from the bundled Figtree font, so the logo has
no live text. rsvg-convert renders the PNG files, and optipng (on PATH)
interlaces them, which the brands guide prefers.
"""

from __future__ import annotations

import math
from pathlib import Path
import shutil
import subprocess

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "brand" / "fonts" / "Figtree-Variable.ttf"
BRAND = ROOT / "custom_components" / "sun_sweep" / "brand"
SOURCES = ROOT / "brand"
WORDMARK = "Sun Sweep"
WEIGHT = 600

# The set's family colours: the warm brown outline and wordmark shared with
# House Structure and Manual J, the gold of Thermal Lab, and its orange.
# The pale wedge is the set's gold at a lower opacity, so the swept part
# (sunrise to now) stands clear of the day's arc, and the sun sits apart
# from the swept gold.
BROWN = "#4e342e"
CREAM = "#f7f4ef"
PALE_HEX = "#f0d58a"
PALE_OPACITY = 0.55
STRONG_HEX = "#d99a00"
SUN_HEX = "#e0562b"
# On a dark dashboard the brown outline vanishes, so the light tones swap.
LIGHT = {
    "ring": BROWN,
    "house": CREAM,
    "edge": BROWN,
    "sun_edge": BROWN,
    "pale_opacity": PALE_OPACITY,
    "ink": BROWN,
}
DARK = {
    "ring": "#f4efe6",
    "house": "#2b1f1b",
    "edge": "#f4efe6",
    "sun_edge": "#f4efe6",
    "pale_opacity": 0.5,
    "ink": "#f4efe6",
}

# Geometry in master units: a 512 square, centred on 256.
CENTRE = 256.0
RIM = 184.0
# The ring is heavier than the card's, so it still reads at a few dozen
# pixels. At 40 px it is about 2.7 px wide.
RING = 34.0
HOUSE_STROKE = 30.0
SUN_RADIUS = RIM / 5.45
SUN_STROKE = 12.0
# A northern summer day: sunrise in the north-east, sun mid-morning, sunset north-west.
RISE, NOW, SET = 48.0, 108.0, 314.0


def _at(azimuth: float, radius: float) -> tuple[float, float]:
    turn = math.radians(azimuth)
    return CENTRE + radius * math.sin(turn), CENTRE - radius * math.cos(turn)


def _sector(start: float, end: float) -> list[tuple[float, float]]:
    span = (end - start) % 360.0
    steps = max(2, int(span / 3))
    points = [(CENTRE, CENTRE)]
    for step in range(steps + 1):
        points.append(_at(start + span * step / steps, RIM))
    return points


def _house() -> list[tuple[float, float]]:
    """An L-shaped plan, about 34% of the rim's radius each way."""
    scale = RIM * 0.34
    # east, north
    corners = [
        (-1.0, -0.7),
        (1.0, -0.7),
        (1.0, 0.15),
        (0.1, 0.15),
        (0.1, 0.7),
        (-1.0, 0.7),
    ]
    return [(CENTRE + east * scale, CENTRE - north * scale) for east, north in corners]


def _points(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def _mark_box() -> tuple[float, float, float, float]:
    """The mark's ink: the ring's outer edge and the sun's outer edge."""
    sun_x, sun_y = _at(NOW, RIM)
    outer = RIM + RING / 2
    reach = SUN_RADIUS + SUN_STROKE / 2
    left = min(CENTRE - outer, sun_x - reach)
    right = max(CENTRE + outer, sun_x + reach)
    top = min(CENTRE - outer, sun_y - reach)
    bottom = max(CENTRE + outer, sun_y + reach)
    return left, top, right, bottom


def _mark(dark: bool) -> str:
    """The mark's shapes, in master units, in drawing order."""
    tone = DARK if dark else LIGHT
    sun_x, sun_y = _at(NOW, RIM)
    return (
        f'<polygon id="pale" points="{_points(_sector(RISE, SET))}" '
        f'fill="{PALE_HEX}" fill-opacity="{tone["pale_opacity"]}"/>'
        f'<polygon id="strong" points="{_points(_sector(RISE, NOW))}" '
        f'fill="{STRONG_HEX}"/>'
        f'<circle id="ring" cx="{CENTRE:.2f}" cy="{CENTRE:.2f}" r="{RIM:.2f}" '
        f'fill="none" stroke="{tone["ring"]}" stroke-width="{RING:.2f}"/>'
        f'<polygon id="house" points="{_points(_house())}" fill="{tone["house"]}" '
        f'stroke="{tone["edge"]}" stroke-width="{HOUSE_STROKE:.2f}" '
        f'stroke-linejoin="miter"/>'
        f'<circle id="sun" cx="{sun_x:.2f}" cy="{sun_y:.2f}" r="{SUN_RADIUS:.2f}" '
        f'fill="{SUN_HEX}" stroke="{tone["sun_edge"]}" stroke-width="{SUN_STROKE:.2f}"/>'
    )


def _wordmark(height: float, left: float, centre: float, dark: bool) -> tuple[str, tuple]:
    """The wordmark as one outlined path, its cap height centred on ``centre``.

    Returns the path and its ink bounds (xMin, yMin, xMax, yMax).
    """
    font = instantiateVariableFont(TTFont(FONT), {"wght": WEIGHT})
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    scale = height / font["head"].unitsPerEm
    cap = font["OS/2"].sCapHeight * scale
    baseline = centre + cap / 2
    path = SVGPathPen(glyphs, ntos=lambda value: f"{value:.2f}")
    bounds = BoundsPen(glyphs)
    x = left
    for char in WORDMARK:
        name = cmap[ord(char)]
        transform = (scale, 0, 0, -scale, x, baseline)
        glyphs[name].draw(TransformPen(path, transform))
        glyphs[name].draw(TransformPen(bounds, transform))
        x += hmtx[name][0] * scale
    ink = DARK["ink"] if dark else LIGHT["ink"]
    markup = f'<path id="wordmark" fill="{ink}" d="{path.getCommands()}"/>'
    return markup, bounds.bounds


def _icon_svg(dark: bool) -> str:
    left, top, right, bottom = _mark_box()
    side = max(right - left, bottom - top)
    mid_x, mid_y = (left + right) / 2, (top + bottom) / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{mid_x - side / 2:.2f} '
        f'{mid_y - side / 2:.2f} {side:.2f} {side:.2f}">{_mark(dark)}</svg>\n'
    )


def _logo_svg(dark: bool) -> str:
    left, top, right, bottom = _mark_box()
    height = bottom - top
    # The set's logos leave a gap of 0.203 of the logo height between the mark
    # and the wordmark. Figtree's left side bearing adds about 0.025 to it.
    # Cap height is 0.40 of the logo height, the same as the set's other logos.
    # Figtree's cap height is 0.70 em.
    text_height = height * 0.40 / 0.70
    gap = height * 0.178
    wordmark, (_, _, text_right, _) = _wordmark(text_height, right + gap, CENTRE, dark)
    width_right = max(right, text_right)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left:.2f} {top:.2f} '
        f'{width_right - left:.2f} {height:.2f}">{_mark(dark)}{wordmark}</svg>\n'
    )


def _render(svg: Path, png: Path, *, width: int | None, height: int | None) -> None:
    tool = shutil.which("rsvg-convert")
    if tool is None:
        raise SystemExit("rsvg-convert is required to render the brand images")
    size = [] if width is None else ["-w", str(width)]
    size += [] if height is None else ["-h", str(height)]
    subprocess.run([tool, *size, "-o", str(png), str(svg)], check=True)
    optipng = shutil.which("optipng")
    if optipng is None:
        raise SystemExit("optipng is required to write interlaced brand images")
    subprocess.run([optipng, "-i", "1", "-o", "2", "-quiet", str(png)], check=True)


def main() -> None:
    SOURCES.mkdir(parents=True, exist_ok=True)
    BRAND.mkdir(parents=True, exist_ok=True)
    masters = {
        "icon": _icon_svg(False),
        "dark_icon": _icon_svg(True),
        "logo": _logo_svg(False),
        "dark_logo": _logo_svg(True),
    }
    for name, markup in masters.items():
        (SOURCES / f"{name}.svg").write_text(markup, encoding="utf-8")
    for name in masters:
        svg = SOURCES / f"{name}.svg"
        if name.endswith("icon"):
            _render(svg, BRAND / f"{name}.png", width=256, height=256)
            _render(svg, BRAND / f"{name}@2x.png", width=512, height=512)
        else:
            _render(svg, BRAND / f"{name}.png", width=None, height=256)
            _render(svg, BRAND / f"{name}@2x.png", width=None, height=512)


if __name__ == "__main__":
    main()
