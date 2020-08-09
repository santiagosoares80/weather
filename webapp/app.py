from flask import Flask, render_template, request, redirect, flash, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import datetime
import matplotlib.pyplot as plt
import io
import base64
import os
from functools import wraps

app = Flask (__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Set secret key
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application")
else:
    app.secret_key = SECRET_KEY

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# From: https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
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


@app.route("/capabilities", methods=["GET", "POST"])
def capabilities():
	# User wants to delete a capability
	if request.method == "POST":
		# Get what capability the user wants to delete
		capability = request.form.get('capability')

		# Open connection with database
		conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

		# Enable foreign keys on sqlite3
		conn.execute("PRAGMA foreign_keys = ON")
		c = conn.cursor()

		# Check if any probe uses the capability
		probe = c.execute("SELECT * FROM probe_capabilities WHERE capability_id = ?", (capability,)).fetchone()

		# If any probe implements the capability, we cannot delete
		if not probe is None:
			flash("This capability is used by some probe and cannot be deleted")
			conn.close()
			return redirect(url_for('capabilities'))
		else:
			# The capability is not used by any probe, let's delete it
			c.execute("DELETE FROM capabilities WHERE id = ?", (capability,))

			# Check if the capability was deleted
			if c.rowcount == 1:
				flash("The capability was deleted succesfully")
			else:
				flash("Something went wrong and the capability was not deleted")

			# Commit modifications
			conn.commit()

			# Close connection
			conn.close()

			# Return to capabilities screen
			return redirect(url_for('capabilities'))

	if request.method == "GET":
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

@app.route("/login", methods=["GET", "POST"])
def login():
	"""Log user in"""

	# Forget any user_id
	session.clear()

	# User reached route via POST (as by submitting a form via POST)
	if request.method == "POST":

		# Ensure username was submitted
		if not request.form.get("username"):
			flash("Must provide a username")
			return render_template('login.html')

		# Ensure password was submitted
		elif not request.form.get("password"):
			flash("Must provide a password")
			return render_template('login.html')

		# Open connection with database
		conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

		# Enable foreign keys on sqlite3
		conn.execute("PRAGMA foreign_keys = ON")
		c = conn.cursor()

		# Query database for username
		rows = c.execute("SELECT id, username, hash, admin FROM users WHERE username = ?", (request.form.get("username"),)).fetchone()

		# Close database connection
		conn.close()
		app.logger.info(rows)
		# Ensure username exists and password is correct
		if rows is None or not check_password_hash(rows[2], request.form.get("password")):
			flash("Invalid username and/or password")
			return render_template('login.html')

		# Remember which user has logged in
		session["user_id"] = rows[0]
		session["username"] = rows[1]
		session["admin"] = rows[3]

		# Redirect user to home page
		return redirect("/")

	# User reached route via GET (as by clicking a link or via redirect)
	else:
		return render_template("login.html")


@app.route("/logout")
def logout():
	"""Log user out"""

	# Forget any user_id
	session.clear()

	# Redirect user to login form
	return redirect("/")


if __name__ == '__main__': app.run(debug=True, port = 80, host = '0.0.0.0')

