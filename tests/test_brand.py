# Copyright (c) 2026 MinchinWeb
"""Brand images follow the Home Assistant integration brands guide."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

BRAND = (
    Path(__file__).resolve().parents[1] / "custom_components" / "sun_sweep" / "brand"
)

# Square icons are 256 and 512. A logo's short side is 128-256, or 256-512
# at double resolution, and the top of that range is preferred. Trimmed
# means the subject meets the canvas on its long axis.
_ICON = {
    "icon.png": 256,
    "dark_icon.png": 256,
    "icon@2x.png": 512,
    "dark_icon@2x.png": 512,
}
_LOGO = {
    "logo.png": (128, 256),
    "dark_logo.png": (128, 256),
    "logo@2x.png": (256, 512),
    "dark_logo@2x.png": (256, 512),
}


def test_icons_are_square_trimmed_pngs():
    for name, side in _ICON.items():
        image = Image.open(BRAND / name)
        assert image.format == "PNG"
        assert image.size == (side, side)
        assert image.mode == "RGBA"
        assert image.info.get("interlace")
        _reaches_the_edge(image)


def test_logos_are_landscape_and_as_tall_as_allowed():
    for name, (low, high) in _LOGO.items():
        image = Image.open(BRAND / name)
        assert image.format == "PNG"
        assert image.mode == "RGBA"
        assert image.info.get("interlace")
        short = min(image.size)
        assert image.width > image.height
        assert short == high
        assert low <= short <= high
        _reaches_the_edge(image)


def _reaches_the_edge(image: Image.Image) -> None:
    box = image.getchannel("A").getbbox()
    assert box is not None
    left, top, right, bottom = box
    width, height = image.size
    assert min(left, top, width - right, height - bottom) <= 2
