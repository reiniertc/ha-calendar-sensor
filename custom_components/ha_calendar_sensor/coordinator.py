# coordinator.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


@dataclass
class AgendaEvent:
    start: datetime
    end: Optional[datetime]
    summary: str
    description: Optional[str]


class AgendaCoordinator(DataUpdateCoordinator[Dict[int, List[AgendaEvent]]]):
    """Coordinator die agenda-events ophaalt, per dag indeelt en aan de sensors levert."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        calendar_entity: str,
        days_ahead: int,
        max_events: int,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=name,
            update_interval=update_interval,
        )
        self._calendar_entity = calendar_entity
        self._days_ahead = days_ahead
        self._max_events = max_events

    @property
    def days_ahead(self) -> int:
        return self._days_ahead

    @property
    def max_events(self) -> int:
        return self._max_events

    async def _async_update_data(self) -> Dict[int, List[AgendaEvent]]:
        """Haal events op en groepeer per dag-index."""
        now = dt_util.now()
        tz = now.tzinfo
        today = now.date()

        events_by_day: Dict[int, List[AgendaEvent]] = {}

        async with async_timeout.timeout(30):
            for day_index in range(self._days_ahead):
                day = today + timedelta(days=day_index)

                start_dt = datetime.combine(day, datetime.min.time()).replace(tzinfo=tz)
                end_dt = datetime.combine(day, datetime.max.time()).replace(tzinfo=tz)

                response = await self.hass.services.async_call(
                    "calendar",
                    "get_events",
                    {
                        "entity_id": self._calendar_entity,
                        "start_date_time": start_dt.isoformat(),
                        "end_date_time": end_dt.isoformat(),
                    },
                    blocking=True,
                    return_response=True,
                )

                calendar_data = response.get(self._calendar_entity, {})
                raw_events = calendar_data.get("events", [])

                day_events: List[AgendaEvent] = []

                for ev in raw_events[: self._max_events]:
                    start_raw = ev.get("start")
                    end_raw = ev.get("end")

                    start = self._parse_datetime_like(start_raw, tz)
                    if start is None:
                        # Als start niet parsebaar is, sla dit event over
                        continue

                    end = self._parse_datetime_like(end_raw, tz) if end_raw else None

                    day_events.append(
                        AgendaEvent(
                            start=start,
                            end=end,
                            summary=ev.get("summary") or "",
                            description=ev.get("description"),
                        )
                    )

                events_by_day[day_index] = day_events

        _LOGGER.debug(
            "AgendaCoordinator update %s: %s",
            self._calendar_entity,
            {k: len(v) for k, v in events_by_day.items()},
        )

        return events_by_day

    @staticmethod
    def _parse_datetime_like(
        value: Optional[str],
        tz,
    ) -> Optional[datetime]:
        """Probeer een string als datetime of date te parsen en timezone toe te voegen."""
        if not value:
            return None

        # Probeer eerst volledige datetime
        dt = dt_util.parse_datetime(value)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            return dt

        # Anders als date
        date = dt_util.parse_date(value)
        if date is not None:
            return datetime.combine(date, datetime.min.time()).replace(tzinfo=tz)

        return None
