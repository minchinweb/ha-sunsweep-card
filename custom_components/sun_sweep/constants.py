# Copyright (c) 2026 MinchinWeb
"""Names and colours shared by the integration and the card drawing."""

from __future__ import annotations

DOMAIN = "sun_sweep"
PLATFORMS = ["sensor"]

# House Structure keeps the building ring here (latitude, longitude corners).
# It is optional: without it the card draws a plain square.
HOUSE_STRUCTURE = "house_structure"
OUTLINE_DATA = "house_structure_outline"
# Its "Building outline" sensor: found, not_found, failed or not_loaded.
OUTLINE_SENSOR = "{}_outline"

CARD_PATH = "/sun_sweep_static"
# The query changes when the card script changes, so a browser does not
# keep a copy that failed to load.
CARD_URL = f"{CARD_PATH}/sun-sweep-card.js?v=8"
DOCS = (
    "https://github.com/minchinweb/ha-sunsweep-card/blob/master/docs/configuration.md"
)

# The card draws these, in this order. drawing.py is the reference.
PALE = "#f6d84a"
PALE_OPACITY = 0.35
STRONG = "#f0b429"
STRONG_OPACITY = 0.72
HOUR = "#c48a12"
TWILIGHT = "#9aafc9"
TWILIGHT_OPACITY = 0.55
RING = "#111111"
SUN_FILL = "#f5c400"
SUN_STROKE = "#a56b00"
# Cool grey so the white half of the two-tone moon still reads.
MOON_FILL = "#c5d0dc"
MOON_STROKE = "#8aa0b8"
HOUSE_FILL = "#f7f4ef"
HOUSE_STROKE = "#3d4a57"

ABOVE = "above_horizon"
BELOW = "below_horizon"
