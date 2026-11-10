# Copyright (c) 2026 MinchinWeb
"""One entry. The outline comes from House Structure, so there is nothing to type."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
import voluptuous as vol

from .constants import DOMAIN, OUTLINE_DATA

HOUSE = "house_structure"


class SunSweepConfigFlow(ConfigFlow, domain=DOMAIN):
    """Confirm that House Structure has a building outline."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the entry once an outline is available."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if not self.hass.config_entries.async_entries(HOUSE):
            return self.async_abort(reason="house_structure_missing")
        info = self.hass.data.get(OUTLINE_DATA) or {}
        if info.get("failed") or not info.get("points"):
            return self.async_abort(reason="no_outline")
        if user_input is not None:
            return self.async_create_entry(title="Sun Sweep", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
