from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from homeassistant.const import CONF_SCAN_INTERVAL

from .const import (
    DOMAIN,
    CONF_CALENDAR_ENTITY,
    CONF_DAYS_AHEAD,
    CONF_MAX_EVENTS,
    DEFAULT_DAYS_AHEAD,
    DEFAULT_MAX_EVENTS,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
)


class HaCalendarSensorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            calendar_entity = user_input[CONF_CALENDAR_ENTITY]
            days_ahead = user_input[CONF_DAYS_AHEAD]
            max_events = user_input[CONF_MAX_EVENTS]

            await self.async_set_unique_id(calendar_entity)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"HA Calendar Sensor: {calendar_entity}",
                data={
                    CONF_CALENDAR_ENTITY: calendar_entity,
                    CONF_DAYS_AHEAD: days_ahead,
                    CONF_MAX_EVENTS: max_events,
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_CALENDAR_ENTITY): selector(
                    {"entity": {"domain": "calendar"}}
                ),
                vol.Required(CONF_DAYS_AHEAD, default=DEFAULT_DAYS_AHEAD): vol.All(
                    int, vol.Range(min=1, max=7)
                ),
                vol.Required(CONF_MAX_EVENTS, default=DEFAULT_MAX_EVENTS): vol.All(
                    int, vol.Range(min=1, max=24)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            # data komt in entry.options terecht
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current,
                ): vol.All(
                    int,
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
