# Copyright (c) 2026 MinchinWeb
"""The card can ask for the sweep on a chosen date."""

from __future__ import annotations

from custom_components.sun_sweep import async_setup

LAT, LON = 53.5461, -113.4938


def _place(hass) -> None:
    hass.config.latitude = LAT
    hass.config.longitude = LON
    hass.config.time_zone = "America/Edmonton"


async def test_a_pinned_afternoon_is_a_winter_day(hass, hass_ws_client) -> None:
    _place(hass)
    assert await async_setup(hass, {})
    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "sun_sweep/snapshot",
            "date": "2026-12-21",
            "time": "15:00",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["phase"] == "day"
    assert msg["result"]["sun_elevation"] > 0


async def test_a_bad_date_is_refused(hass, hass_ws_client) -> None:
    _place(hass)
    assert await async_setup(hass, {})
    client = await hass_ws_client(hass)
    await client.send_json({"id": 2, "type": "sun_sweep/snapshot", "date": "June"})
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_date"
