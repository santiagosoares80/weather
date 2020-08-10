from flask import Flask, render_template, request, redirect, flash, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import datetime
import matplotlib.pyplot as plt
import io
import base64
import os
import secrets
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

def chgpwd_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('chgpwd'):
             return redirect(url_for('changepasswd'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            flash("You are not an admin")
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
@chgpwd_required
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
@login_required
@chgpwd_required
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
@login_required
@chgpwd_required
@admin_required
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
@login_required
@chgpwd_required
@admin_required
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

@app.route("/users", methods=["GET", "POST"])
@login_required
@chgpwd_required
@admin_required
def users():
	# User wants to delete a capability
	if request.method == "POST":
		# Get what capability the user wants to delete
		userid = request.form.get('userid')

		# Open connection with database
		conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

		# Enable foreign keys on sqlite3
		conn.execute("PRAGMA foreign_keys = ON")
		c = conn.cursor()

		# Let's check if the user is not trying to delete himself
		username = c.execute("SELECT username FROM users WHERE id = ?", (userid,)).fetchone()

		# Check if the user exists
		if username is None:
			flash(f"There's no user with id {userid}")
			conn.close()
			return redirect(url_for('users'))
		# The user cannot delete himself
		elif username[0] == session['username']:
			flash(f"User cannot delete himself")
			conn.close()
			return redirect(url_for('users'))
		else:
			# Let's delete the user
			c.execute("DELETE FROM users WHERE id = ?", (userid,))

			# Check if the user was deleted
			if c.rowcount == 1:
				flash("The user was deleted succesfully")
			else:
				flash("Something went wrong and the user was not deleted")

			# Commit modifications
			conn.commit()

			# Close connection
			conn.close()

			# Return to users screen
			return redirect(url_for('users'))

	if request.method == "GET":
		# Open connection with database
		conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

		# Enable foreign keys on sqlite3
		conn.execute("PRAGMA foreign_keys = ON")
		c = conn.cursor()

		# Get capabilities
		users = c.execute("SELECT id, first_name, last_name, username, admin FROM users").fetchall()

		# Close connection to the database
		conn.close()

		return render_template('users.html', users = users)

@app.route("/adduser", methods=["GET", "POST"])
@login_required
@chgpwd_required
@admin_required
def adduser():

	# User reaches via POST method
	if request.method == "POST":
		# Ensure fields are not empty
		if not request.form.get("username") or not request.form.get("firstname") or not request.form.get("lastname"):
			flash("Fields must not be empty")
			return render_template('adduser.html')

		username = request.form.get("username")
		firstname = request.form.get("firstname")
		lastname = request.form.get("lastname")
		if request.form.get("admin"):
			admin = 1
		else:
			admin = 0

		# Open connection with database
		conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

		# Enable foreign keys on sqlite3
		conn.execute("PRAGMA foreign_keys = ON")
		c = conn.cursor()

		# Check if username exist
		capability = c.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
		if not capability is None:
			flash("Username already taken")
			conn.close()
			return render_template('adduser.html')

		# Generate random password
		passwd = secrets.token_urlsafe(16)

		# Insert capability into database
		c.execute("INSERT INTO users (username, first_name, last_name, hash, admin) VALUES (?, ?, ?, ?, ?)", 
				(username, firstname, lastname, generate_password_hash(passwd), admin))

		# Commit modifications
		conn.commit()

		# Close connection to the database
		conn.close()

		# Check if user was correctly created
		if c.rowcount == 1:
			flash(f"New user created. Password {passwd}")
		else:
			flash("Error - User was not created")

		# Get back to capabilities
		return redirect("/users")

	else:
		return render_template('adduser.html')


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
		rows = c.execute("SELECT id, username, hash, admin, chgpwd FROM users WHERE username = ?", (request.form.get("username"),)).fetchone()

		# Close database connection
		conn.close()

		# Ensure username exists and password is correct
		if rows is None or not check_password_hash(rows[2], request.form.get("password")):
			flash("Invalid username and/or password")
			return render_template('login.html')

		# Remember which user has logged in
		session["user_id"] = rows[0]
		session["username"] = rows[1]
		session["admin"] = rows[3]
		session["chgpwd"] = rows[4]

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

@app.route("/changepasswd", methods=["GET", "POST"])
@login_required
def changepasswd():

	# User reaches via POST
	if request.method == "POST":

		# Checks if all fiels where filled and if passwords match
		if not request.form.get("oldpasswd"):
			flash("Must provide old password")
			return redirect(url_for('changepasswd'))
		elif not request.form.get("newpasswd"):
			flash("Must provide new password")
			return redirect(url_for('changepasswd'))
		elif not request.form.get("confirm"):
			flash("Must confirm new password")
			return redirect(url_for('changepasswd'))
		elif request.form.get("newpasswd") != request.form.get("confirm"):
			flash("Passwords must match")
			return redirect(url_for('changepasswd'))
		elif request.form.get("oldpasswd") == request.form.get('newpasswd'):
			flash("New password must be different from old password")
			return redirect(url_for('changepasswd'))

		# Open connection with database
		conn = sqlite3.connect("/home/pi/projects/weather/weather.db")

		# Enable foreign keys on sqlite3
		conn.execute("PRAGMA foreign_keys = ON")
		c = conn.cursor()

		# Select user from database
		rows = c.execute("SELECT id, username, hash FROM users WHERE id = ?", (session["user_id"],)).fetchone()

		# Check if old passwd match
		if rows is None or not check_password_hash(rows[2], request.form.get("oldpasswd")):
			flash("invalid password")
			conn.close()
			return redirect(url_for('changepasswd'))
		# Change passwd
		else:
			c.execute("UPDATE users SET hash = ?, chgpwd = 0 WHERE id = ?", (generate_password_hash(request.form.get("newpasswd")), session["user_id"]))

		# Commit modifications
		conn.commit()

		# Close connection to database
		conn.close()

		# Verifies if password updated succesfully
		if c.rowcount == 1:
			session['chgpwd'] = False
			flash("Password changed succesfully")
		else:
			Flash("Error - password not changed")

		return redirect("/")

	# User reaches via GET
	else:
		return render_template("changepasswd.html")


if __name__ == '__main__': app.run(debug=True, port = 80, host = '0.0.0.0')

