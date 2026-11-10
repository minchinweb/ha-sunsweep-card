# Copyright (c) 2026 MinchinWeb
"""The config flow asks for nothing, even when the outline is missing."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sun_sweep.config_flow import SunSweepConfigFlow
from custom_components.sun_sweep.constants import DOMAIN, OUTLINE_DATA


def _flow(hass: HomeAssistant) -> SunSweepConfigFlow:
    flow = SunSweepConfigFlow()
    flow.hass = hass
    flow.handler = DOMAIN
    return flow


async def test_without_house_structure_the_entry_is_still_created(
    hass: HomeAssistant,
) -> None:
    flow = _flow(hass)
    result = await flow.async_step_user()
    assert result["type"] is FlowResultType.FORM
    result = await flow.async_step_user({})
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_a_missing_outline_still_creates_the_entry(hass: HomeAssistant) -> None:
    MockConfigEntry(domain="house_structure", data={}).add_to_hass(hass)
    flow = _flow(hass)
    result = await flow.async_step_user()
    assert result["type"] is FlowResultType.FORM
    result = await flow.async_step_user({})
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_the_entry_is_created_when_the_outline_is_there(
    hass: HomeAssistant,
) -> None:
    MockConfigEntry(domain="house_structure", data={}).add_to_hass(hass)
    hass.data[OUTLINE_DATA] = {
        "points": [(0.0, 0.0), (0.0, 0.001), (0.001, 0.0)],
        "rotation": 0.0,
    }
    flow = _flow(hass)
    result = await flow.async_step_user()
    assert result["type"] is FlowResultType.FORM
    result = await flow.async_step_user({})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Sun Sweep"
    assert result["data"] == {}


async def test_only_one_entry(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, data={}).add_to_hass(hass)
    MockConfigEntry(domain="house_structure", data={}).add_to_hass(hass)
    hass.data[OUTLINE_DATA] = {"points": [(0.0, 0.0), (0.0, 0.001), (0.001, 0.0)]}
    result = await _flow(hass).async_step_user()
    assert result["reason"] == "single_instance_allowed"
