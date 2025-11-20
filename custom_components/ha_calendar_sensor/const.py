from datetime import timedelta
from homeassistant.const import CONF_SCAN_INTERVAL

DOMAIN = "ha_calendar_sensor"

CONF_CALENDAR_ENTITY = "calendar_entity"
CONF_DAYS_AHEAD = "days_ahead"
CONF_MAX_EVENTS = "max_events"

DEFAULT_DAYS_AHEAD = 2
DEFAULT_MAX_EVENTS = 12

# scan-interval in minuten (te gebruiken in options flow)
DEFAULT_SCAN_INTERVAL = 15
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 120
