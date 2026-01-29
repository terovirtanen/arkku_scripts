# https://www.waveshare.com/wiki/Pico-ePaper-7.5-B

# https://github.com/waveshareteam/Pico_ePaper_Code/blob/main/python/Pico-ePaper-7.5-B.py

# text, line, rectangle, circle, ellipse, polygon, arc
# https://docs.micropython.org/en/latest/library/framebuf.html


from umqtt.simple import MQTTClient
import ubinascii
import time
import network
# own library
import config

print(dir(time))
print(time.ticks_us())

def debug_print(message):
    """Print message if debug is True, otherwise do nothing."""
    if debug:
        print(message)

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.soft_reset()

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

def wlan_connect():
    # network connection setup    
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

    return wlan


def sub_cb(topic, msg):
  print((topic, msg))
  if topic == config.mqtt_topic_outdoor_temperature:
    print('Outdoor temperature received: %s °C' % msg.decode())

def mqtt_connect_and_subscribe():
#   global client_id, mqtt_server, mqtt_topic
  client = MQTTClient(config.client_id, config.mqtt_server, user=config.mqtt_user, password=config.mqtt_pass)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(config.mqtt_topic)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (config.mqtt_server, config.mqtt_topic))
  return client

def listen_for_messages(client):
    try:
        while True:
            # Check for new messages
            client.check_msg()
            # Alternative: Use wait_msg() to block until a message arrives
            # client.wait_msg()
            time.sleep(10)
    finally:
        client.disconnect()


try:
  wlan = wlan_connect()
  client = mqtt_connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()


listen_for_messages(client)

restart_and_reconnect()