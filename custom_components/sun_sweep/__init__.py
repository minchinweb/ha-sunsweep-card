# Copyright (c) 2026 MinchinWeb
"""Sun Sweep: today's sun angles around the house, top down.

The building outline comes from House Structure
(``hass.data["house_structure_outline"]``). This integration works out the
sun and the moon and serves the Lovelace card.
"""

from __future__ import annotations

from pathlib import Path

from .constants import CARD_PATH, CARD_URL, DOMAIN, PLATFORMS


async def async_setup(hass, config) -> bool:
    """Serve the card and the snapshot command."""
    from homeassistant.components import frontend
    from homeassistant.components.http import StaticPathConfig
    from homeassistant.setup import async_when_setup

    from .api import async_register

    async_register(hass)

    if hass.http is None:
        return True
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_PATH, str(Path(__file__).parent / "frontend"), False)]
    )

    async def _register_card(_hass, _component) -> None:
        frontend.add_extra_js_url(hass, CARD_URL)

    async_when_setup(hass, "frontend", _register_card)
    return True


async def async_setup_entry(hass, entry) -> bool:
    """Start the minute-by-minute sweep and its sensor."""
    from .coordinator import SunSweepCoordinator

    coordinator = SunSweepCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry) -> bool:
    """Remove the sensor."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# Re-exported so other code can find the domain without importing Home Assistant.
__all__ = ["DOMAIN"]
