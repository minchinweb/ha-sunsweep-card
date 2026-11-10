# Copyright (c) 2026 MinchinWeb
"""The Lovelace drawing matches the Python reference, including its colours."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess

from custom_components.sun_sweep import constants
from custom_components.sun_sweep.drawing import card_svg

_drawing_spec = importlib.util.spec_from_file_location(
    "sun_sweep_test_drawing",
    Path(__file__).resolve().parent / "test_drawing.py",
)
_drawing_tests = importlib.util.module_from_spec(_drawing_spec)
_drawing_spec.loader.exec_module(_drawing_tests)
SUMMER = _drawing_tests.SUMMER

ROOT = Path(__file__).resolve().parents[1]
DRAWING = ROOT / "custom_components" / "sun_sweep" / "frontend" / "drawing.js"

# Colours the card paints. Stroke-only constants stay in Python.
_CARD_COLOURS = (
    "PALE",
    "STRONG",
    "HOUR",
    "TWILIGHT",
    "RING",
    "SUN_FILL",
    "MOON_FILL",
    "HOUSE_FILL",
    "HOUSE_STROKE",
)


def test_frontend_colours_match_the_constants():
    source = DRAWING.read_text(encoding="utf-8")
    for name in _CARD_COLOURS:
        assert getattr(constants, name) in source


def test_frontend_svg_matches_the_reference():
    cases = (
        (SUMMER, None),
        (SUMMER, {"rotation": -20}),
        (SUMMER, {"show_sun": False, "show_moon": False, "show_hours": False}),
        ({**SUMMER, "twilight_start": 20.0, "twilight_end": 340.0}, None),
        ({"outline": []}, None),
    )
    for attrs, options in cases:
        rendered = _node_svg(attrs, options)
        assert rendered == card_svg(attrs, options)


def _node_svg(attrs: dict, options: dict | None) -> str:
    completed = subprocess.run(
        ["node", str(ROOT / "tests" / "render_frontend.mjs")],
        input=json.dumps({"attrs": attrs, "options": options}),
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout
