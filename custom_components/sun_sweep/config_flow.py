# Copyright (c) 2026 MinchinWeb
"""One entry. The outline comes from House Structure, so there is nothing to type."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
import voluptuous as vol

from .constants import DOMAIN


class SunSweepConfigFlow(ConfigFlow, domain=DOMAIN):
    """Confirm the sweep. House Structure is optional."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the entry.

        The card draws a square until House Structure has a building outline.
        A missing outline does not block setup.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="Sun Sweep", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
