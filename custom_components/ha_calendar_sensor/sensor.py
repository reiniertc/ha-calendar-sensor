from __future__ import annotations

from datetime import datetime
from typing import Any, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
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


class AgendaDaySensor(CoordinatorEntity, SensorEntity):
    """One sensor per day with event_0..event_N attributes."""

    _attr_icon = "mdi:calendar"
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: AgendaCoordinator,
        calendar_entity: str,
        day_index: int,
        max_events: int,
    ) -> None:
        super().__init__(coordinator)
        self.coordinator: AgendaCoordinator = coordinator
        self._calendar_entity = calendar_entity
        self._day = day_index
        self._max_events = max_events

        # Gebruik deel na de punt als basisnaam, bv. "ical_andersom"
        if "." in calendar_entity:
            slug = calendar_entity.split(".", 1)[1]
        else:
            slug = calendar_entity

        self._calendar_slug = slug

        # Entity-id wordt: sensor.<slug>_day_<index>
        # voorbeeld: sensor.ical_andersom_day_0
        self._attr_name = f"{slug}_day_{day_index}"

        # Unique id moet uniek zijn per kalender + dag
        self._attr_unique_id = f"ha-calendar-sensor-{slug}-day-{day_index}"

    @property
    def native_value(self) -> int:
        """Return number of events as an integer."""
        events = self.coordinator.data.get(self._day, [])
        return len(events)

    def _normalize_time(self, value: Any) -> str:
        """Zet verschillende tijdformaten om naar 'HH:MM' of leeg."""
        if value is None:
            return ""

        # Als het al een datetime is
        if isinstance(value, datetime):
            dt = value
        else:
            # Verwacht string; probeer eerst datetime, dan date
            s = str(value)
            dt = dt_util.parse_datetime(s)
            if dt is None:
                d = dt_util.parse_date(s)
                if d is None:
                    return ""
                dt = datetime.combine(d, datetime.min.time())

        dt_local = dt_util.as_local(dt)
        return dt_local.strftime("%H:%M")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        event_0..event_N in formaat:
        'HH:MM-HH:MM Titel' of 'HH:MM Titel' als eindtijd ontbreekt.
        """
        attrs: dict[str, Any] = {}

        events = self.coordinator.data.get(self._day, [])

        for idx, ev in enumerate(events):
            # Ondersteun zowel AgendaEvent als dict uit calendar-service
            if isinstance(ev, dict):
                start_raw = ev.get("start")
                end_raw = ev.get("end")
                summary = ev.get("summary") or ""
            else:
                start_raw = getattr(ev, "start", None)
                end_raw = getattr(ev, "end", None)
                summary = getattr(ev, "summary", "") or ""

            start_str = self._normalize_time(start_raw)
            end_str = self._normalize_time(end_raw)

            if start_str and end_str:
                value = f"{start_str}-{end_str} {summary}"
            elif start_str:
                value = f"{start_str} {summary}"
            else:
                value = summary

            attrs[f"event_{idx}"] = value

        attrs["count"] = len(events)

        if self.coordinator.last_update_success_time:
            attrs["last_refresh"] = dt_util.as_local(
                self.coordinator.last_update_success_time
            ).isoformat()

        return attrs
