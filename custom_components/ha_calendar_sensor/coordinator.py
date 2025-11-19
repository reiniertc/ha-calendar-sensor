from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util


@dataclass
class AgendaEvent:
    start: datetime
    end: datetime | None
    summary: str
    description: str | None


class AgendaCoordinator(DataUpdateCoordinator[dict[int, list[AgendaEvent]]]):
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
            logger=None,
            name=name,
            update_interval=update_interval,
        )
        self._calendar_entity = calendar_entity
        self._days_ahead = days_ahead
        self._max_events = max_events

    async def _async_update_data(self):
        tz = dt_util.get_default_time_zone()
        today = dt_util.now(tz=tz).date()

        results = {}

        async with async_timeout.timeout(30):
            for index in range(self._days_ahead):
                day = today + timedelta(days=index)
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

                data = response.get(self._calendar_entity, {})
                raw_events = data.get("events", [])

                events = []
                for ev in raw_events[: self._max_events]:
                    start = dt_util.parse_datetime(ev.get("start"))
                    end = dt_util.parse_datetime(ev.get("end")) if ev.get("end") else None

                    events.append(
                        AgendaEvent(
                            start=start or start_dt,
                            end=end,
                            summary=ev.get("summary", ""),
                            description=ev.get("description"),
                        )
                    )

                results[index] = events

        return results
