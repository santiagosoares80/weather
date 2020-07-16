import pigpio
import vw
import time

#GPIO pin for receiver
RXPin = 27

#Radio rate in bps
rate = 2000

#This server address
address = 1

pi = pigpio.pi()
receiver = vw.rx(pi, RXPin, rate)

print("Starting receiver")

#Runs forever listening to messages
while True:
	time.sleep(0.5)
	message = []

	#Receive message, a list of Ints
	while receiver.ready():
		message = [c for c in receiver.get()]

	#If there is no message, end iteration
	if not message:
		continue

	#Decode message
	#First get the destination address
	destination = message[0]

	#Check if message is to us, if it's not, ignore message
	if not destination == address:
		print("Message not to server")
		continue

	#Get source
	source = message[1]

	#Get flags
	flags = message[3]

	#Get content of the message as a string
	content = "".join(chr(c) for c in message[4:])

	#print content of the message
	if flags == 16:
		print(f"We received a control message from {source}: {content}.")
	elif flags == 1:
		print(f"We received temperature from {source}: {content}ºC")
	elif flags == 2:
		print(f"We received humidity from {source}: {content}%")
	else:
		print("We received an unexpected message")

receiver.cancel()
pi.stop()
