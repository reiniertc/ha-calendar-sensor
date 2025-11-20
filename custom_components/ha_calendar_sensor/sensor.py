# sensor.py
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Zet de sensor op via config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HaCalendarSensor(coordinator, entry)])


class HaCalendarSensor(CoordinatorEntity, SensorEntity):
    """Sensor die op basis van de AgendaCoordinator de agenda exposeert."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        SensorEntity.__init__(self)

        self._attr_unique_id = f"{entry.entry_id}_day_0"
        self._attr_name = "Agenda day 0"

    @property
    def native_value(self) -> Any:
        """Aantal afspraken vandaag."""
        data = self.coordinator.data or {}
        return data.get("count_today", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Alle event_* attributen + last_refresh en count_today."""
        data = self.coordinator.data or {}
        attrs: dict[str, Any] = {}

        for k, v in data.items():
            if isinstance(k, str) and k.startswith("event_"):
                attrs[k] = v

        if "last_refresh" in data:
            attrs["last_refresh"] = data["last_refresh"]

        if "count_today" in data:
            attrs["count_today"] = data["count_today"]

        return attrs
