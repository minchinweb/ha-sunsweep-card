# Copyright (c) 2026 MinchinWeb
"""``translations/en.json`` is ``strings.json``."""

from __future__ import annotations

import json
from pathlib import Path

PKG = Path(__file__).parent.parent / "custom_components" / "sun_sweep"


def test_english_matches_strings():
    strings = (PKG / "strings.json").read_text(encoding="utf-8")
    english = (PKG / "translations" / "en.json").read_text(encoding="utf-8")
    assert json.loads(english) == json.loads(strings)
    assert "[%key:" not in strings
