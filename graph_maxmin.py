import sqlite3
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from sys import argv, exit

# Check number of arguments
if len(argv) != 2:
    exit("Usage: python graph.py days")

# Check if argument is a number
if not argv[1].isnumeric():
    exit("Days must be an integer")

# Check if argument is an integer
if not float(argv[1]).is_integer():
    exit("Days must be an integer")

# Days to plot
days = argv[1]

# Open connection with database
conn = sqlite3.connect("/home/pi/projects/weather/weather.db")
#conn.set_trace_callback(print)

# Enable foreign keys on sqlite3
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

# Get all probes and capabilities
probes = c.execute("SELECT * FROM probes").fetchall()

# List of all graphs to be plotted
graphs = []

# Read data to be plotted for each capability of each probe
for probe in probes:
    # List the capabilities of each probe
    capabilities = c.execute("SELECT pb.capability_id, cp.description, cp.unit FROM probe_capabilities AS pb \
                              JOIN capabilities AS cp ON pb.capability_id = cp.id WHERE probe_id = ?", (str(probe[0]),)).fetchall()

    # Select max and min daily values from each capability of each probe
    for capability in capabilities:
        maxmin = c.execute("SELECT MAX(CAST(value AS INT)), MIN(CAST(value AS INT)), date(datetime) FROM measurements \
                         WHERE probe_id = ? AND measurement_type = ? \
                         AND datetime > datetime('now', 'localtime', ?) \
                         GROUP BY date(datetime)", (str(probe[0]), str(capability[0]), f"-{days} day")).fetchall()

        # Convert tuples to lists
        max_values = [float(data[0].replace('\x00','')) if type(data[0]) == str else data[0] for data in maxmin]
        min_values = [float(data[1].replace('\x00','')) if type(data[1]) == str else data[1] for data in maxmin]
        dates = [datetime.datetime.strptime(data[2], "%Y-%m-%d") for data in maxmin] 

        # Append data to graphs to be plotted
        graphs.append({'probe_id': probe[0], 'probe': probe[1], 'capability_id': capability[0], 'capability': capability[1], 'unit': capability[2], 'max_values': max_values, 'min_values': min_values, 'dates': dates })

#Close connection to the database
conn.close()

for graph in graphs:
    plt.rcParams["figure.figsize"] = [5,4]
    fig, ax = plt.subplots(1,1)
    ax.plot(graph['dates'], graph['max_values'], linestyle='-', color=f"C{graph['capability_id'] + 2}", label='Max')
    ax.plot(graph['dates'], graph['min_values'], linestyle='-', color=f"C{graph['capability_id'] - 1}", label='Min')
    fig.autofmt_xdate()
    if(int(days) <= 3):
        formatter = mdates.DateFormatter("%H:%M")
    elif(int(days) < 10):
        formatter = mdates.DateFormatter("%a")
    else:
        formatter = mdates.DateFormatter("%d/%b")
    ax.xaxis.set_major_formatter(formatter)
    ax.set_xlim(left=datetime.datetime.now() - datetime.timedelta(days=int(days)))
    ax.set_title(f"{graph['probe']} - {graph['capability']}")
    ax.set_xlabel('Time')
    ax.set_ylabel(f"{graph['capability']} ({graph['unit']})")
    ax.legend()
    ax.grid(b=True)
    plt.savefig(f"/home/pi/projects/weather/webapp/static/images/{graph['probe_id']}_{graph['capability']}_{days}_maxmin.png")
    plt.close()
