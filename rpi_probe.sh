#!/bin/bash

temp=$(vcgencmd measure_temp | grep -oP "(?<=temp=).*?(?=')")
probeid=11
capabilitytemp=3
capabilitycpu=6

sqlite3 /home/pi/projects/weather/weather.db "INSERT INTO measurements (measurement_type, probe_id, value, datetime) VALUES ($capabilitytemp, $probeid, $temp, datetime('now', 'localtime'));"

prev_cpu=/home/pi/projects/weather/cpu
IFS=' '
read -r -a cpu_usage <<< $(head -1 /proc/stat | sed 's/.\{4\}//')
cpu_total=0
cpu_idle=${cpu_usage[3]}

for cpu in ${cpu_usage[@]}
do
	cpu_total=$(($cpu_total+$cpu))
done

if [ -f $prev_cpu ]
then
	read -r -a prev_cpu_usage <<< $(cat $prev_cpu)
	prev_cpu_total=${prev_cpu_usage[0]}
	prev_cpu_idle=${prev_cpu_usage[1]}
	cpu_busy=$((100-(100*(cpu_idle-prev_cpu_idle)/(cpu_total-prev_cpu_total))))
	sqlite3 /home/pi/projects/weather/weather.db "INSERT INTO measurements (measurement_type, probe_id, value, datetime) VALUES ($capabilitycpu, $probeid, $cpu_busy, datetime('now', 'localtime'));"
fi
echo $cpu_total $cpu_idle > /home/pi/projects/weather/cpu
