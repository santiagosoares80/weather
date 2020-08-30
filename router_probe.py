from pysnmp.hlapi import *
from sys import exit
from datetime import datetime
import syslog
import secret_keys
import pickle
import os
import sqlite3

COMMUNITY = secret_keys.community
ROUTERIP = '192.168.15.39'
FILE = '/home/pi/projects/weather/snmp'
DATABASE = '/home/pi/projects/weather/weather.db'
PROBEID = 12
DOWNLOADID = 4
UPLOADID = 5

errorIndication, errorStatus, errorIndex, varBinds = next(
    getCmd(SnmpEngine(),
           CommunityData(COMMUNITY),
           UdpTransportTarget((ROUTERIP, 161)),
           ContextData(),
           ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10.8')),
           ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.16.8')))
)

if errorIndication:
    syslog.syslog(errorIndication)
    exit()
elif errorStatus:
    syslog.syslog('%s at %s' % (errorStatus.prettyPrint(),
                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    exit()
else:
    inOctets = float(varBinds[0][1])
    outOctets = float(varBinds[1][1])

collectTime = datetime.now()

currentdata = {'collectTime': collectTime, 'inOctets': inOctets, 'outOctets': outOctets}

if os.path.exists(FILE) and os.path.getsize(FILE) > 0:
        with open(FILE, 'rb') as f:
            previousdata = pickle.load(f)
        delta = currentdata['collectTime'] - previousdata['collectTime']

        # Check if counters restarted
        if currentdata['inOctets'] >= previousdata['inOctets']:
            deltain = currentdata['inOctets'] - previousdata['inOctets']
        else:
            deltain = currentdata['inOctets'] + (4294967295 - previousdata['inOctets'])

        if currentdata['outOctets'] >= previousdata['outOctets']:
            deltaout = currentdata['outOctets'] - previousdata['outOctets']
        else:
            deltaout = currentdata['outOctets'] + (4294967295 - previousdata['outOctets'])

	# Calculate throughput
        inBand = (deltain) * 8 / delta.seconds / 1000000
        outBand = (deltaout) * 8 / delta.seconds / 1000000

        # Insert data on database
        conn = sqlite3.connect(DATABASE)
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("INSERT INTO measurements (measurement_type, probe_id, value, datetime) VALUES (?, ?, ?, datetime('now', 'localtime'))",
		(DOWNLOADID, PROBEID, float(f"{float(inBand):.2f}")))
        c.execute("INSERT INTO measurements (measurement_type, probe_id, value, datetime) VALUES (?, ?, ?, datetime('now', 'localtime'))",
		(UPLOADID, PROBEID, float(f"{float(outBand):.2f}")))
        conn.commit()
        conn.close()

with open(FILE, 'wb') as f:
    f.seek(0)
    pickle.dump(currentdata, f)
    f.truncate()

syslog.syslog("Router Probe SNMP: Data collected allright")
