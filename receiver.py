import pigpio
import vw
import time

RXPin = 27
rate = 2000

pi = pigpio.pi()
receiver = vw.rx(pi, RXPin, rate)

start = time.time()

print("Starting receiver")
while True:
	while receiver.ready():
		message = "".join(chr(c) for c in receiver.get())
		# First 2 chars of message are 0xff 0xff, don't know why, just discard them
		message = message[2:]
		print(message)
	time.sleep(2)

receiver.cancel()
pi.stop()
