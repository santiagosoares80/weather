#!/bin/bash

temp=$(vcgencmd measure_temp | grep -oP "(?<=temp=).*?(?=')")
probeid=11
capabilityid=3

sqlite3 /home/pi/projects/weather/weather.db "INSERT INTO measurements (measurement_type, probe_id, value, datetime) VALUES ($capabilityid, $probeid, $temp, datetime('now', 'localtime'));"
