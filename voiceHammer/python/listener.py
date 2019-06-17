import pyaudio
import wave
import requests
import json
import RPi.GPIO as GPIO
import time

print("Listener booting...")

#setup raspberry pi General Purpose Input Output (GPIO)
GPIO.setmode(GPIO.BOARD) #numbers on board, 2, 4, 6 , 8 etc from corner which says 'made in uk'
GPIO.setup(8, GPIO.OUT) #setup pin 8 for output Blue
GPIO.setup(10, GPIO.OUT) #setup pin 10 for output yellow
GPIO.setup(12, GPIO.OUT) #setup pin 12 for output flames
GPIO.setup(22, GPIO.OUT) #setup pin 22 for output pump
GPIO.setup(38, GPIO.OUT) #setup pin 38 for output actuator left
GPIO.setup(40, GPIO.OUT) #setup pin 40 for output actuator right

goIn = GPIO.PWM(38,50)
goOut = GPIO.PWM(40,50)#50 is freqency

goIn.start(0)
goOut.start(0)

#ideally dont have this in the code, read it from config file
url = 'https://toothcommandapi.azurewebsites.net/api/Commander?code=A7xxxxxxxxxxxxxQQ=='
audio = pyaudio.PyAudio()
wav_output_filename = 'recording.wav' 


#create a bunch of functions that will be called later on
def smokeOff():
    print("smoke off")
    goIn.start(30)#% duty cycle!! like 30% power
    time.sleep(0.5)
    goIn.stop()

def smokeOn():
    print("smoke on")
    goOut.start(30)
    time.sleep(0.5)
    goOut.stop()

def pumpOn():
    print("pump on!")
    GPIO.output(22,GPIO.HIGH)

def pumpOff():
    print("pump off!")
    GPIO.output(22,GPIO.LOW)

def blueLightOn():
    print("blue light on!")
    GPIO.output(8,GPIO.HIGH)

def blueLightOff():
    print("blue light off!")
    GPIO.output(8,GPIO.LOW)

def yellowLightOn():
    print("yellow light on!")
    GPIO.output(10,GPIO.HIGH)

def yellowLightOff():
    print("yellow light off!")
    GPIO.output(10,GPIO.LOW)

def flameLightOn():
    print("flame light on!")
    GPIO.output(12,GPIO.HIGH)

def flameLightOff():
    print("flame light off!")
    GPIO.output(12,GPIO.LOW)


#function that records audio as .wav file
def recordWaveFile():
    form_1 = pyaudio.paInt16 # 16-bit resolution
    chans = 1 # 1 channel
    samp_rate = 44100 # 44.1kHz sampling rate
    chunk = 4096 # 2^12 samples for buffer
    record_secs = 3 # seconds to record
    dev_index = 2# device index found by p.get_device_info_by_index(ii)
    # create pyaudio stream
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=chunk)
    print("recording...")
    yellowLightOn()
    frames = []
    # loop through stream and append audio chunks to frame array
    for ii in range(0,int((samp_rate/chunk)*record_secs)):
        data = stream.read(chunk)
        frames.append(data)
    print("finished recording")
    yellowLightOff()
    stream.stop_stream()
    stream.close()
    # save the audio frames as .wav file
    wavefile = wave.open(wav_output_filename,'wb')
    wavefile.setnchannels(chans)
    wavefile.setsampwidth(audio.get_sample_size(form_1))
    wavefile.setframerate(samp_rate)
    wavefile.writeframes(b''.join(frames))
    wavefile.close()


#send the request to the API and get status code back
def sendRequest():
    print("time to send request....")
    audiofile = open(wav_output_filename, "rb")
    r = requests.get(url, data= audiofile)
    return r.status_code
    
#based on the status code enact different actions, lights on/off etc..
def processRequestResult(statusCode):
    print(statusCode)
    if(statusCode == 200):
        flameLightOn()
        playWaveFile('lightsOn.wav')
        print('make ready for combat. lights on. 200')
    if(statusCode == 202):
        blueLightOn() 
        playWaveFile('lightsOff.wav')          
        flameLightOff()     
        time.sleep(2)
        blueLightOff()
        print('cool the forge. lights off. 202')
    if(statusCode == 201):
        smokeOn()
        pumpOn()
        playWaveFile('toothbreakerignite2.wav')
        print('tooth breaker ignite. attack! 201')
        smokeOff()
        pumpOff()
    if(statusCode == 204):
        playWaveFile('NoOnlyToast.wav')
        blueLightOn() 
        time.sleep(1)
        blueLightOff()
        print('make me a sandwich. joke. 204')


#play audio file
def playWaveFile(filename):
    #define stream chunk   
    chunk = 1024  
    f = wave.open(filename,"rb")  
    #open stream  
    stream = audio.open(format = audio.get_format_from_width(f.getsampwidth()),  
                    channels = f.getnchannels(),  
                    rate = f.getframerate(),  
                    output = True)  
    #read data  
    data = f.readframes(chunk)  
    #play stream  
    while data:  
        stream.write(data)  
        data = f.readframes(chunk)  

    stream.stop_stream()  
    stream.close()  


#main loop. record audio, send it to API, then process the result. then keep doing that forever unless cancelled by user
try:

    while True:
        recordWaveFile()
        result = sendRequest()
        processRequestResult(result)

except KeyboardInterrupt:
    pass

print("Listener closing...")

#tidy up all the GPIO so that we don't leave the lights on
GPIO.output(8,GPIO.LOW)
GPIO.output(10,GPIO.LOW)
GPIO.output(12,GPIO.LOW)
GPIO.output(22,GPIO.LOW)
goIn.stop()
goOut.stop()
audio.terminate() 
GPIO.cleanup


print("all done")