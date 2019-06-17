print("finding device index...")

import pyaudio
p = pyaudio.PyAudio()
for ii in range(p.get_device_count()):
     print(p.get_device_info_by_index(ii).get('name'))


#expected output:

# bcm2835 ALSA: - (hw:0,0)              <---This is index 0
# bcm2835 ALSA: IEC958/HDMI (hw:0,1)    <---This is index 1
# Webcam C170: USB Audio (hw:1,0)       <---This is index 2 (so for me I use index 2)
# sysdefault
# default
# dmix