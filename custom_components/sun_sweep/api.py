# Copyright (c) 2026 MinchinWeb
"""A snapshot for one chosen moment, so a card can be pinned while debugging."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
import voluptuous as vol

from .constants import HOUSE_STRUCTURE, OUTLINE_DATA
from .sweep import finish_snapshot, resolve_when


@websocket_api.websocket_command(
    {
        vol.Required("type"): "sun_sweep/snapshot",
        vol.Optional("date"): str,
        vol.Optional("time"): str,
    }
)
@websocket_api.async_response
async def ws_snapshot(hass: HomeAssistant, connection, msg: dict) -> None:
    """The sweep at a date, using the home location and the saved outline."""

    installed = bool(hass.config_entries.async_entries(HOUSE_STRUCTURE))

    def build() -> dict:
        now = datetime.now(ZoneInfo(hass.config.time_zone))
        when = resolve_when(now, msg.get("date"), msg.get("time"), hass.config.latitude)
        info = hass.data.get(OUTLINE_DATA) or {}
        points = [] if info.get("failed") else info.get("points") or []
        return finish_snapshot(
            when,
            hass.config.latitude,
            hass.config.longitude,
            points,
            house_structure=installed,
        )

    try:
        result = await hass.async_add_executor_job(build)
    except TypeError, ValueError:
        connection.send_error(
            msg["id"],
            "invalid_date",
            "Use a date like 2026-06-21, and a time like 09:30.",
        )
        return
    connection.send_result(msg["id"], result)


def async_register(hass: HomeAssistant) -> None:
    """Register the snapshot command. The decorator only tags the handler."""
    websocket_api.async_register_command(hass, ws_snapshot)
