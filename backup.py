"""
Backup of the Weather Database to Dropbox
"""

import dropbox
import secret_keys
import sqlite3
from sys import exit
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

TOKEN = secret_keys.dropbox_key

DATABASE = '/home/pi/projects/weather/weather.db'

LOCALFILE = '/home/pi/projects/weather/weather_dump.sql'

BACKUPPATH = '/weather_dump.sql'

RPI_PROBEID = 11

BACKUP_EVENT_TYPE = 32

# Dump the database for backup.
conn = sqlite3.connect(DATABASE)
iterator = conn.iterdump()
with open(LOCALFILE, 'w') as f:
    for line in iterator:
        f.write(f"{line}\n")
conn.close()

# Create an instance of a Dropbox class, which can make requests to the API.
dbx = dropbox.Dropbox(TOKEN)
# Check that the access token is valid
try:
    dbx.users_get_current_account()
except AuthError:
    exit("ERROR: Invalid access token; try re-generating an "
                 "access token from the app console on the web.")
message = ''
# Open file as binary for reading
with open(LOCALFILE, 'rb') as f:
    try:
        # Tries to upload the file
        dbx.files_upload(f.read(), BACKUPPATH, mode=WriteMode('overwrite'))
        message = 'Backup done!'
    except ApiError:
        # This checks for the specific error where a user doesn't have
        # enough Dropbox space quota to upload this file
        if (err.error.is_path() and  err.error.get_path().reason.is_insufficient_space()):
            message = "ERROR: Cannot back up; insufficient space."
        elif err.user_message_text:
            message = err.user_message_text
        else:
            message = err

# Insert backup event on database
conn = sqlite3.connect(DATABASE)
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()
c.execute("INSERT INTO events (event_type_id, probe_id, log, datetime) VALUES (?, ?, ?, datetime('now', 'localtime'))", 
		(BACKUP_EVENT_TYPE, RPI_PROBEID, message,))
conn.commit()
conn.close()
exit()
