from flask import Flask, render_template, request, redirect, flash
import sqlite3
import datetime
import matplotlib.pyplot as plt
import io
import base64

app = Flask (__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Set secret key to sign cookies
app.secret_key = b'B6Nw8elUskuG1dZNGLwGbA'

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
			data[3] = datetime.datetime.strptime(data[3], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")

		# Insert each probe with the last measurements to the cards list
		cards.append([ probe[0], probe[1], lastdata])

	# Close connection to the database
	conn.close()

	return render_template("index.html", cards = cards)

@app.route("/graphs")
def graphs():

	# Get probe ID from args of URL
	probe = request.args.get('probe')

	# Open connection with database
	conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

	# Enable foreign keys on sqlite3
	conn.execute("PRAGMA foreign_keys = ON")
	c = conn.cursor()

	# Get probe capabilities
	capabilities = c.execute("SELECT cp.description FROM capabilities AS cp JOIN probe_capabilities AS pc \
                                  ON cp.id = pc.capability_id WHERE pc.probe_id = ?", (probe,)).fetchall()

	# Transform tuples in list
	capabilities = [capability[0].replace("'","") for capability in capabilities]

	#Close connection to the database
	conn.close()

	return render_template('graphs.html', probe=probe, capabilities=capabilities)


@app.route("/capabilities")
def capabilities():
	# Open connection with database
	conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

	# Enable foreign keys on sqlite3
	conn.execute("PRAGMA foreign_keys = ON")
	c = conn.cursor()

	# Get capabilities
	capabilities = c.execute("SELECT id, description, unit FROM capabilities").fetchall()

	# Close connection to the database
	conn.close()

	return render_template('capabilities.html', capabilities = capabilities)


@app.route("/addcap", methods=["GET", "POST"])
def add_cap():

	# User reaches via POST method
	if request.method == "POST":
		# Ensure fields are not empty
		if not request.form.get("capability") or not request.form.get("unit"):
			flash("Fields must not be empty")
			return render_template('addcap.html')

		newcap = request.form.get("capability")
		unit = request.form.get("unit")

		# Open connection with database
		conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

		# Enable foreign keys on sqlite3
		conn.execute("PRAGMA foreign_keys = ON")
		c = conn.cursor()

		# Check if capability exist
		capability = c.execute("SELECT id FROM capabilities WHERE description = ?", (newcap,)).fetchone()
		if not capability is None:
			flash("Capability already exist")
			return render_template('addcap.html')

		# Insert capability into database
		c.execute("INSERT INTO capabilities (description, unit) VALUES (?, ?)", (newcap,unit))

		# Commit modifications
		conn.commit()

		# Close connection to the database
		conn.close()

		# Get back to capabilities
		return redirect("/capabilities")
		
	else:
		return render_template('addcap.html')

if __name__ == '__main__': app.run(debug=False, port = 80, host = '0.0.0.0')

