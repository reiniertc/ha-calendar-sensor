# coordinator.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
import logging

import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


@dataclass
class AgendaEvent:
    start: str
    end: str
    summary: str
    description: str | None


class AgendaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator die agenda-events ophaalt en vlakke data voor de sensor aanlevert."""

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

    async def _async_update_data(self) -> dict[str, Any]:
        now = dt_util.now()
        tz = now.tzinfo
        today = now.date()

        payload: dict[str, Any] = {}
        total_today = 0

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

                events = raw_events[: self._max_events]

                if day_index == 0:
                    total_today = len(events)

                for event_index, ev in enumerate(events):
                    evt = AgendaEvent(
                        start=ev.get("start", ""),
                        end=ev.get("end", ""),
                        summary=ev.get("summary", ""),
                        description=ev.get("description"),
                    )

                    prefix = f"event_{day_index}_{event_index}"
                    payload[f"{prefix}_start"] = evt.start
                    payload[f"{prefix}_end"] = evt.end
                    payload[f"{prefix}_summary"] = evt.summary
                    payload[f"{prefix}_description"] = evt.description or ""

        payload["count_today"] = total_today
        payload["last_refresh"] = dt_util.utcnow().isoformat()

        _LOGGER.debug(
            "AgendaCoordinator update %s: count_today=%s, keys=%s",
            self._calendar_entity,
            total_today,
            list(payload.keys()),
        )

        return payload
