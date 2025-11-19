from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_DAYS_AHEAD, CONF_MAX_EVENTS
from .coordinator import AgendaCoordinator, AgendaEvent


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AgendaCoordinator = hass.data[DOMAIN][entry.entry_id]

    days = entry.data[CONF_DAYS_AHEAD]
    max_events = entry.data[CONF_MAX_EVENTS]

    entities = [
        AgendaDaySensor(coordinator, day_index=i, max_events=max_events)
        for i in range(days)
    ]

    add_entities(entities)


class AgendaDaySensor(SensorEntity):
    """One sensor per day with up to N event_x attributes."""

    _attr_icon = "mdi:calendar"
    _attr_should_poll = False

    def __init__(self, coordinator: AgendaCoordinator, day_index: int, max_events: int):
        self.coordinator = coordinator
        self._day = day_index
        self._max_events = max_events
        self._attr_name = f"Agenda day {day_index}"
        self._attr_unique_id = f"ha-calendar-sensor-day-{day_index}"

    @property
    def native_value(self):
        events = self.coordinator.data.get(self._day, [])
        return f"{len(events)} events"

    @property
    def extra_state_attributes(self):
        events: list[AgendaEvent] = self.coordinator.data.get(self._day, [])
        tz = dt_util.get_default_time_zone()

        attrs: dict[str, str] = {}
        for i, e in enumerate(events[: self._max_events], start=1):
            t = e.start.astimezone(tz).strftime("%H:%M")
            attrs[f"event_{i}"] = f"{t} {e.summary}"

        return attrs
