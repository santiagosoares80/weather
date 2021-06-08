# weather
This is my final project for CS50.
It's a monitoring sytem made using Python, Flask, SQLite3.
It receives data from probes that can be hardware probes or software probes. The software probes can run on the server and write directly to the database, or run in remote machines, and send data through the network (a receiver software on server side is outside of the scope of the project).
I have implemented a hardware probe using Arduino with C code, that sends the data to the server through a 433MHz radio.
