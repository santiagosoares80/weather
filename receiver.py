import pigpio
import vw
import time

RXPin = 20
rate = 2000

pi = pigpio.pi()
receiver = vw.rx(pi, RXPin, rate)

start = time.time()

for i in range(60):
	while receiver.ready():
		print("Iteration")
		print("".join(chr (c) for c in receiver.get()))

	time.sleep(1)
	print(i)

receiver.cancel()
pi.stop()
