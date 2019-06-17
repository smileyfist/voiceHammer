import RPi.GPIO as GPIO
import time


#this script was used during testing to turn lights etc on for 10 seconds while i was wiring it all up

GPIO.setmode(GPIO.BOARD) #numbers on board, 2, 4, 6 , 8 etc from corner which says 'made in uk'

GPIO.setup(8, GPIO.OUT) #setup pin 8 for output Blue
GPIO.setup(10, GPIO.OUT) #setup pin 10 for output yellow
GPIO.setup(12, GPIO.OUT) #setup pin 12 for output flames
GPIO.setup(22, GPIO.OUT) #setup pin 22 for output pump
GPIO.setup(38, GPIO.OUT) #setup pin 38 for output actuator left
GPIO.setup(40, GPIO.OUT) #setup pin 40 for output actuator right


try:
    print("should light!")
    #GPIO.output(8,GPIO.HIGH)
    #GPIO.output(10,GPIO.HIGH)
    GPIO.output(12,GPIO.HIGH)
    #GPIO.output(22,GPIO.HIGH)


    time.sleep(10)
    
except KeyboardInterrupt:
    pass

print("clean up light!")

GPIO.output(8,GPIO.LOW)
GPIO.output(10,GPIO.LOW)
GPIO.output(12,GPIO.LOW)
GPIO.output(22,GPIO.LOW)
print("all done")

GPIO.cleanup