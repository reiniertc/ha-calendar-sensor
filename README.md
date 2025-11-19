# HA Calendar Sensor

Custom integration that generates sensors for multiple days of events from a Home Assistant calendar entity.

Features:
- Choose a calendar entity (e.g., `calendar.ical_andersom`)
- Choose number of days ahead (1–7)
- Choose max events per day (1–24)
- Creates sensors:  
  - `sensor.agenda_day_0` (today)  
  - `sensor.agenda_day_1` (tomorrow)  
  - ...  
- Each sensor exposes attributes:
  - `event_1`, `event_2`, ... `"HH:MM Title"`

Perfect for e-ink dashboards (ESPHome).
