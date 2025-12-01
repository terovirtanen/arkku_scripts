



import time
print(dir(time))
print(time.ticks_us())

# hx711_gpio.py needs to copy to pico root or to lib/ -directory
from hx711_gpio import HX711
from machine import Pin

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

hx711.tare()

while True:
    value_raw = hx711.read_average()
    value = hx711.get_value()
    print("Weight value raw: " + str(value_raw))
    print("Weight value    : " + str(value))
    time.sleep(1)