from flask import Flask, render_template
import sqlite3
import datetime

app = Flask (__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
	# Open connection with database
	conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

	# Enable foreign keys on sqlite3
	conn.execute("PRAGMA foreign_keys = ON")
	c = conn.cursor()

	# Get probes
	probes = c.execute("SELECT * FROM probes").fetchall()

	# List of data measured
	cards = []

	# Read last measurements for each probe
	for probe in probes:
		# List the capabilities of each probe
		capabilities = c.execute("SELECT capability_id FROM probe_capabilities WHERE probe_id = ?", (str(probe[0]),)).fetchall()
		lastdata = []
		for capability in capabilities:
			lastdata.append(c.execute("SELECT capability.description, measure.value, capability.unit, measure.datetime \
						FROM measurements AS measure JOIN capabilities AS capability ON measure.measurement_type = capability.id \
						WHERE measure.probe_id = ? and capability.id = ? \
						ORDER BY measure.id DESC LIMIT 1", (str(probe[0]),str(capability[0]))).fetchone())
		# Convert tuples to lists
		lastdata = [list(data) for data in lastdata]

		# Remove '\x00' from end of values and format time of last measurement
		for data in lastdata:
			data[1] = data[1].replace('\x00','')
			data[3] = datetime.datetime.strptime(data[3], "%H:%M:%S %d/%m/%y").strftime("%H:%M")

		# Insert each probe with the last measurements to the cards list
		cards.append([ probe[1], lastdata])

	# Close connection to the database
	conn.close()

	return render_template("index.html", cards = cards)

if __name__ == '__main__':
	app.run(debug=False, port = 80, host = '0.0.0.0')
