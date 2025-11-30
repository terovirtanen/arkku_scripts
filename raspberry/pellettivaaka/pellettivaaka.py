
# Example for Pycom device, gpio mode
# Connections:
# Pin # | HX711
# ------|-----------
# P5    | data_pin
# P6   | clock_pin
#

from hx711_gpio import HX711
from machine import Pin

# Initialize HX711
pin_OUT = Pin("P5", Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin("P6", Pin.OUT)

hx711 = HX711(pin_SCK, pin_OUT)

hx711_offset = 0
hx711.set_offset(hx711_offset)
value = hx711.read()
value = hx711.get_value()
print("Weight init value: " + str(value))

# network connection setup
import time
import network
ssid = 'Wireless Network'
password = 'The Password'
 
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
status = wlan.ifconfig()
print( 'ip = ' + status[0] )

# main loop
while True:

    # Do things here, perhaps measure something using a sensor?
    # value = hx711.read()
    value = hx711.get_value()
    print("Weight value: " + str(value))

    # todo: send scale value to remote end point

    # ...and then define the headers and payloads
    # headers = ...
    # payload = ...
    
    # Then send it in a try/except block
    # try:
    #     print("sending...")
    #     response = requests.post("A REMOTE END POINT", headers=headers, data=payload)
    #     print("sent (" + str(response.status_code) + "), status = " + str(wlan.status()) )
    #     response.close()
    # except:
    #     print("could not connect (status =" + str(wlan.status()) + ")")
    #     if wlan.status() < 0 or wlan.status() >= 3:
    #         print("trying to reconnect...")
    #         wlan.disconnect()
    #         wlan.connect(ssid, password)
    #         if wlan.status() == 3:
    #             print('connected')
    #         else:
    #             print('failed')

    time.sleep(5)