# Copyright (c) 2026 MinchinWeb
"""Read the house outline and work out the sweep once a minute."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .constants import DOMAIN, OUTLINE_DATA
from .sweep import snapshot

_LOGGER = logging.getLogger(__name__)

type SunSweepConfigEntry = ConfigEntry[SunSweepCoordinator]


class SunSweepCoordinator(DataUpdateCoordinator[dict]):
    """The sweep drawn by the card."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self) -> dict:
        return await self.hass.async_add_executor_job(self._read)

    def _read(self) -> dict:
        info = self.hass.data.get(OUTLINE_DATA) or {}
        points = [] if info.get("failed") else info.get("points") or []
        when = datetime.now(ZoneInfo(self.hass.config.time_zone))
        return snapshot(
            when, self.hass.config.latitude, self.hass.config.longitude, points
        )
