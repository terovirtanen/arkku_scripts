# hx711_gpio.py needs to copy to pico root or to lib/ -directory
from hx711_gpio import HX711
from machine import Pin
import urequests as requests

# Initialize HX711
# Example for Pycom device, gpio mode
# Connections:
# Pin # | HX711
# ------|-----------
# P5    | data_pin
# P6   | clock_pin
pin_OUT = Pin(5, Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin(6, Pin.OUT)

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

    # Send scale value to remote endpoint as JSON per API spec
    endpoint = "http://192.168.100.50/pellettivaaka/index.php"
    headers = {"Content-Type": "application/json"}
    payload = {"weight": value, "type": "init"}

    # try:
    #     print("sending...")
    #     response = requests.post(endpoint, headers=headers, json=payload)
    #     print("sent (" + str(response.status_code) + "), status = " + str(wlan.status()) )
    #     # Optionally print response content
    #     try:
    #         print(response.text)
    #     except:
    #         pass
    #     response.close()
    # except Exception as e:
    #     print("could not connect (status=" + str(wlan.status()) + ") error=" + str(e))
    #     if wlan.status() < 0 or wlan.status() >= 3:
    #         print("trying to reconnect...")
    #         try:
    #             wlan.disconnect()
    #         except:
    #             pass
    #         wlan.connect(ssid, password)
    #         if wlan.status() == 3:
    #             print('connected')
    #         else:
    #             print('failed')

    time.sleep(10)