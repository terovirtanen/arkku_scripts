



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

# hx711.tare()
num_samples = 12
samples = []
for i in range(num_samples):
    reading = hx711.read_average()
    samples.append(reading)
    print(f"init: {i+1}: {reading}")
    time.sleep(0.1)
samples.sort()
clean_samples = samples[3:-3] # Remove 3 highest and 3 lowest
# Calculate reference unit
hx711_offset = sum(clean_samples) / len(clean_samples)
print(f"\Offset avg: {hx711_offset:.1f}")
# hx711_offset = hx711.read_average(15)
# hx711.power_down()
#calibrate
known_weight = 3000.0  # grams
print("Scale ready! Place items to weigh…")
time.sleep(10)
# hx711.power_up()
# time.sleep(0.5)
samples = []
for i in range(num_samples):
    reading = hx711.read_average() - hx711_offset
    samples.append(reading)
    print(f"calib {i+1}: {reading}")
    time.sleep(0.1)
# Remove outliers (simple method: remove top and bottom 20%)
samples.sort()
clean_samples = samples[3:-3] # Remove 3 highest and 3 lowest
# Calculate reference unit
average = sum(clean_samples) / len(clean_samples)
reference_unit = average / known_weight # 5.36, 5.21, 5.42
# 18.41
print(f"\nAverage reading: {average:.1f}")
print(f"Reference unit: {reference_unit:.2f}")
print(f"\nAdd this to your script:")
print(f"hx711.set_scale({reference_unit:.2f})")

hx711_offset=610000.0
reference_unit=15.5
while True:
    value_avg = hx711.read_average() - hx711_offset
    value_unit = value_avg / reference_unit
    # hx711.power_down()
    # value = hx711.get_value()
    print("Weight value avg: " + str(value_avg))
    print("Weight value unit: " + str(value_unit/1000) + " kg")
    # print("Weight value    : " + str(value))
    time.sleep(3)

    # hx711.power_up()
    # time.sleep(0.5)
