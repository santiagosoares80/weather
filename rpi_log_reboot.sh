#!/bin/bash

probeid=11
eventtypeid=16
log="Raspberry Pi reboot!"

sqlite3 /home/pi/projects/weather/weather.db "INSERT INTO events (event_type_id, probe_id, log, datetime) VALUES ($eventtypeid, $probeid, '$log', datetime('now', 'localtime'));"
