from flask import Flask
import sqlite3
import datetime

app = Flask (__name__)


@app.route("/")
def index():
	# Open connection with database
	conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

	# Enable foreign keys on sqlite3
	conn.execute("PRAGMA foreign_keys = ON")
	c = conn.cursor()

	# Get capabilities
	capabilities = c.execute("SELECT * FROM capabilities").fetchall()

	# List of data measured
	lastdata = []

	# Read last measurement for each capability
	for capability in capabilities:
		lastdata.append(c.execute("SELECT capability.description, measure.value, capability.unit, measure.datetime FROM measurements AS measure JOIN capabilities AS capability ON measure.measurement_type = capability.id WHERE capability.id = ? ORDER BY measure.id DESC LIMIT 1", str(capability[0])).fetchone())

	# Convert tuples to lists
	lastdata = [list(data) for data in lastdata]

	# Remove '\x00' from end of values
	for data in lastdata:
		data[1] = data[1].replace('\x00','')
		data[3] = datetime.datetime.strptime(data[3], "%H:%M:%S %d/%m/%y").strftime("%H:%M")

	print(lastdata)

	# Close connection to the database
	conn.close()

	return "Hello world"

if __name__ == '__main__':
	app.run(debug=True, port = 80, host = '0.0.0.0')
