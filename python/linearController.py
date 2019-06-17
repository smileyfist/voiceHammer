import RPi.GPIO as GPIO
import time


#this was used to test out the linear actuator as I was wiring it up


GPIO.setmode(GPIO.BOARD) #numbers on board, 2, 4, 6 , 8 etc from corner which says 'made in uk'


GPIO.setup(38, GPIO.OUT) #setup pin 38 for output actuator left
GPIO.setup(40, GPIO.OUT) #setup pin 40 for output actuator right

print("begin!")

goIn = GPIO.PWM(38,50)
goOut = GPIO.PWM(40,50)#50 is freqency

goIn.start(0)
goOut.start(0)


print("in")
goIn.start(30)#% duty cycle!! like 30% power
time.sleep(0.5)
goIn.stop()

print("out")
goOut.start(30)
time.sleep(0.5)
goOut.stop()

 
print("all done")
GPIO.cleanup