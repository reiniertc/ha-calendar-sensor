from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_DAYS_AHEAD,
    CONF_MAX_EVENTS,
    CONF_CALENDAR_ENTITY,
)
from .coordinator import AgendaCoordinator, AgendaEvent


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for each configured day."""
    coordinator: AgendaCoordinator = hass.data[DOMAIN][entry.entry_id]

    days = entry.data[CONF_DAYS_AHEAD]
    max_events = entry.data[CONF_MAX_EVENTS]
    calendar_entity = entry.data[CONF_CALENDAR_ENTITY]

    entities = [
        AgendaDaySensor(
            coordinator=coordinator,
            calendar_entity=calendar_entity,
            day_index=i,
            max_events=max_events,
        )
        for i in range(days)
    ]

    add_entities(entities)


class AgendaDaySensor(SensorEntity):
    """One sensor per day with event_1..event_N attributes."""

    _attr_icon = "mdi:calendar"
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: AgendaCoordinator,
        calendar_entity: str,
        day_index: int,
        max_events: int,
    ) -> None:
        self.coordinator = coordinator
        self._calendar_entity = calendar_entity
        self._day = day_index
        self._max_events = max_events

        # Gebruik deel na de punt als basisnaam, bv. "ical_andersom"
        if "." in calendar_entity:
            slug = calendar_entity.split(".", 1)[1]
        else:
            slug = calendar_entity

        self._calendar_slug = slug

        # Naam zo kiezen dat entity_id wordt: sensor.<slug>_day_<index>
        # voorbeeld: "ical_andersom_day_0" -> sensor.ical_andersom_day_0
        self._attr_name = f"{slug}_day_{day_index}"

        # Unique id moet uniek zijn per kalender + dag
        self._attr_unique_id = f"ha-calendar-sensor-{slug}-day-{day_index}"

    @property
    def native_value(self):
        """Return number of events as an integer."""
        events = self.coordinator.data.get(self._day, [])
        return len(events)

    @property
    def extra_state_attributes(self):
        """
        Alleen event_1..event_N attributen in het formaat:
        'HH:MM-HH:MM Titel' of 'HH:MM Titel' als eindtijd ontbreekt.
        """
        events: list[AgendaEvent] = self.coordinator.data.get(self._day, [])
       
