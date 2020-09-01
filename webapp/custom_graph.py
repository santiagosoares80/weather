import sqlite3
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import base64

from sys import argv, exit
from io import BytesIO

def custom_graph(probeid, capabilities, startdate, enddate):

	# Calculate the number of days to plot
	days = enddate - startdate

	# Open connection with database
	conn = sqlite3.connect("/home/pi/projects/weather/weather.db")
	#conn.set_trace_callback(print)

	# Enable foreign keys on sqlite3
	conn.execute("PRAGMA foreign_keys = ON")
	c = conn.cursor()

	# Retrieve probe name
	probename = c.execute("SELECT description FROM probes WHERE id = ?", (probeid,)).fetchone()

	graphs = []
	# Retrieve data to plot
	for capability in capabilities:

		# Get capabilitiy names and units
		capinfo = ()
		capinfo = c.execute("SELECT description, unit FROM capabilities WHERE id = ?", (capability,)).fetchone()

		# Get measurements for each capability
		lastdata = c.execute("SELECT value, datetime FROM measurements \
				WHERE probe_id = ? AND measurement_type = ? \
				AND datetime >= ? \
				AND datetime <= ?", (probeid, capability, startdate.isoformat(' '), enddate.isoformat(' '))).fetchall()

		# Convert tuples to lists
		values = [float(data[0].replace('\x00','')) if type(data[0]) == str else data[0] for data in lastdata]
		dates = [datetime.datetime.strptime(data[1], "%Y-%m-%d %H:%M:%S") for data in lastdata] 

		# Append data to graphs to be plotted
		graphs.append({'probe_id': probeid, 'probe': probename[0], 'capability_id': capability, 'capability': capinfo[0], 'unit': capinfo[1], 'values': values, 'dates': dates })

	#Close connection to the database
	conn.close()

	# Generate the graphs - Code from matplotlib.org documentation
	plots = []
	for graph in graphs:
		plt.rcParams["figure.figsize"] = [5,4]
		fig, ax = plt.subplots(1,1)
		ax.plot(graph['dates'], graph['values'], linestyle='-', color=f"C{graph['capability_id'] - 1}")
		fig.autofmt_xdate()
		if(int(days.days) <= 3):
			formatter = mdates.DateFormatter("%H:%M")
		elif(int(days.days) < 10):
			formatter = mdates.DateFormatter("%a")
		else:
			formatter = mdates.DateFormatter("%d/%b")
		ax.xaxis.set_major_formatter(formatter)
		ax.set_xlim(left=startdate)
		ax.set_title(f"{graph['probe']} - {graph['capability']}")
		ax.set_xlabel('Time')
		ax.set_ylabel(f"{graph['capability']} ({graph['unit']})")
		ax.grid(b=True)
		buf = BytesIO()
		plt.savefig(buf, format="png")
		data = base64.b64encode(buf.getbuffer()).decode("ascii")
		plots.append(data)

	# Return plots in data:image/png;base64 format
	return plots
