from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.event import async_track_time_interval

from homeassistant.const import CONF_SCAN_INTERVAL

from .const import (
    DOMAIN,
    CONF_CALENDAR_ENTITY,
    CONF_DAYS_AHEAD,
    CONF_MAX_EVENTS,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import AgendaCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    calendar_entity = entry.data[CONF_CALENDAR_ENTITY]
    days_ahead = entry.data[CONF_DAYS_AHEAD]
    max_events = entry.data[CONF_MAX_EVENTS]

    scan_minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    interval = timedelta(minutes=scan_minutes)

    coordinator = AgendaCoordinator(
        hass=hass,
        name=f"Agenda {calendar_entity}",
        calendar_entity=calendar_entity,
        days_ahead=days_ahead,
        max_events=max_events,
        update_interval=interval,
    )

    # eerste refresh + interne DataUpdateCoordinator scheduling
    await coordinator.async_config_entry_first_refresh()

    # extra: eigen interval trigger als fallback
    unsub = async_track_time_interval(
        hass,
        lambda now: coordinator.async_request_refresh(),
        interval,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    # unsub apart opslaan zodat sensor-code niet breekt
    hass.data[DOMAIN][f"{entry.entry_id}_unsub"] = unsub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # timer uitzetten
        unsub = hass.data[DOMAIN].pop(f"{entry.entry_id}_unsub", None)
        if callable(unsub):
            unsub()

        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
