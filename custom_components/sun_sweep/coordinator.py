# Copyright (c) 2026 MinchinWeb
"""Read the house outline and work out the sweep once a minute."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .constants import DOMAIN, HOUSE_STRUCTURE, OUTLINE_DATA
from .outline import outline_status
from .sweep import finish_snapshot

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
        installed = bool(self.hass.config_entries.async_entries(HOUSE_STRUCTURE))
        when = datetime.now(ZoneInfo(self.hass.config.time_zone))
        status = outline_status(self.hass)
        return await self.hass.async_add_executor_job(
            self._read, when, installed, status
        )

    def _read(
        self, when: datetime, house_structure: bool, status: str | None = None
    ) -> dict:
        info = self.hass.data.get(OUTLINE_DATA) or {}
        points = [] if info.get("failed") else info.get("points") or []
        return finish_snapshot(
            when,
            self.hass.config.latitude,
            self.hass.config.longitude,
            points,
            house_structure=house_structure,
            outline_status=status,
        )
