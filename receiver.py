import pigpio
import vw
import time
import sqlite3

from datetime import datetime

#GPIO pin for receiver
RXPin = 27

#Radio rate in bps
rate = 2000

#This server address
address = 1

pi = pigpio.pi()
receiver = vw.rx(pi, RXPin, rate)

print("Starting receiver")

#Set redundant check variables
lastprobe = 0
lastid = 0
lastflag = 0

#Runs forever listening to messages
while True:
	time.sleep(0.5)
	message = []

	#Receive message, a list of Ints
	while receiver.ready():
		message = [c for c in receiver.get()]

	#If there is no message, end iteration
	if not message:
		continue

	#Decode message
	#First get the destination address
	destination = message[0]

	#Check if message is to us, if it's not, ignore message
	if not destination == address:
		print("Message not to server")
		continue

	#Get source probe
	probe = message[1]

	#Get message ID
	id = message[2]

	#Get flags
	flags = message[3]

	#Check if it is not a redundant message
	if (probe == lastprobe and id == lastid and flags == lastflag):
		print("Redundant message")
		continue

	#Set redundancy check variables
	lastprobe, lastid, lastflag = probe, id, flags

	#Get content of the message as a string
	content = "".join(chr(c) for c in message[4:])

	#Open connection with database because we are going to insert something
	conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

	#Enable foreign keys at sqlite3, on a per connection basis
	conn.execute("PRAGMA foreign_keys = ON")
	c = conn.cursor()

	#It's a control message (flags > 15)
	if flags > 15:
		c.execute("INSERT INTO events (event_type_id, probe_id, log, datetime) VALUES (?, ?, ?, datetime('now', 'localtime'))", 
				(flags, probe, content))
	#It's a measurement
	else:
		c.execute("INSERT INTO measurements (measurement_type, probe_id, value, datetime) VALUES (?, ?, ?, datetime('now', 'localtime'))",
				(flags, probe, content))

	#Commit and close connection
	conn.commit()
	conn.close()


	if flags == 16:
		print(f"We received a control message from {probe}: {content}.")
	elif flags == 1:
		print(f"We received temperature from {probe}: {content}ºC")
	elif flags == 2:
		print(f"We received humidity from {probe}: {content}%")
	else:
		print("We received an unexpected message")

receiver.cancel()
pi.stop()
