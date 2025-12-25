# hx711_gpio.py needs to copy to pico root or to lib/ -directory
from hx711_gpio import HX711
from machine import Pin, deepsleep
import urequests as requests
import time
# own library
import config

debug = config.DEBUG
# filename = "debug.txt"

# # Open the file for reading
# r = open(filename, "rt")
# old_data = r.read()
# r.close()

# f = open(filename, "wt")
# f.write(str(old_data) + "\n")

def sleep_or_deepsleep(duration_ms):
    """Sleep for duration_ms milliseconds. Uses sleep if debug=True, otherwise deepsleep."""
    if debug:
        time.sleep(duration_ms / 1000)
    else:
        # f.write(str(duration_ms) + "\n")
        # f.close()
        # deepsleep ei toimi, ei odota vaan tekee resetin heti
        # machine.deepsleep(duration_ms)
        time.sleep(duration_ms / 1000)
        machine.soft_reset()

def debug_print(message):
    """Print message if debug is True, otherwise do nothing."""
    if debug:
        print(message)
    # else: 
    #     f.write(message + "\n")

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

# Do things here, perhaps measure something using a sensor?
# value = hx711.read()
value_avg = hx711.read_average(5) - config.HX711_OFFSET
# value_unit is in kg
value_unit = value_avg / config.REFERENCE_UNIT / 1000

# network connection setup
import network
 
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.WLAN_SSID, config.WLAN_PASSWORD)
# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    debug_print('waiting for connection...')
    debug_print("could not connect (status=" + str(wlan.status()) + ")")
    time.sleep(2)

# Handle connection error
if wlan.status() != 3:
    debug_print('network connection failed')
    sleep_or_deepsleep(30000) # sleep 30 seconds before retry

debug_print("Weight value: " + str(value_unit) + " kg")

# Send scale value to remote endpoint as JSON per API spec
endpoint = "http://192.168.100.50/pellettivaaka/index.php"
headers = {"Content-Type": "application/json"}
payload = {"weight": value_unit, "type": "read"}

try:
    debug_print("sending...")
    response = requests.post(endpoint, headers=headers, json=payload)
    time.sleep(2)
    debug_print("sent (" + str(response.status_code) + "), status = " + str(wlan.status()) )

    response.close()
    wlan.disconnect()

except Exception as e:
    debug_print("could not connect (status=" + str(wlan.status()) + ") error=" + str(e))
    wlan.disconnect()
    sleep_or_deepsleep(15000)  # sleep 60 seconds

# sleep_or_deepsleep(6000)  # sleep 6 seconds
sleep_or_deepsleep(600000)  # sleep 600 seconds / 10 minutes
