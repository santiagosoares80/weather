CREATE TABLE probes (
	id INTEGER NOT NULL PRIMARY KEY,
	description TEXT NOT NULL,
	prbimg TEXT
);

CREATE TABLE capabilities (
	id INTEGER NOT NULL PRIMARY KEY,
	description TEXT NOT NULL,
	unit TEXT,
	icon TEXT
);

CREATE TABLE event_types (
	id INTEGER NOT NULL PRIMARY KEY,
	description TEXT NOT NULL
);

CREATE TABLE probe_capabilities (
	id INTEGER NOT NULL PRIMARY KEY,
	probe_id INTEGER NOT NULL,
	capability_id INTEGER NOT NULL,
	UNIQUE (probe_id, capability_ID),
	FOREIGN KEY (probe_id) REFERENCES probes(id),
	FOREIGN KEY (capability_id) REFERENCES capabilities(id)
);

CREATE TABLE events (
	id INTEGER NOT NULL PRIMARY KEY,
	event_type_id INTEGER NOT NULL,
	probe_id INTEGER NOT NULL,
	log TEXT NOT NULL,
	datetime TEXT NOT NULL,
	FOREIGN KEY (probe_id) REFERENCES probes(id),
	FOREIGN KEY (event_type_id) REFERENCES event_types(id)
);

CREATE TABLE measurements (
	id INTEGER NOT NULL PRIMARY KEY,
	measurement_type INTEGER NOT NULL,
	probe_id INTEGER NOT NULL,
	value REAL NOT NULL,
	datetime TEXT NOT NULL,
	FOREIGN KEY (probe_id, measurement_type) REFERENCES probe_capabilities(probe_id, capability_id)
);

CREATE TABLE users (
	id INTEGER NOT NULL PRIMARY KEY,
	first_name TEXT,
	last_name TEXT,
	username TEXT NOT NULL,
	hash TEXT NOT NULL,
	admin INTEGER NOT NULL,
	chgpwd INTEGER DEFAULT 1 NOT NULL
);

CREATE INDEX measurement ON measurements(measurement_type, probe_id, datetime);

CREATE INDEX event_probe ON events(probe_id);
