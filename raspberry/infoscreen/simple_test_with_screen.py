# https://www.waveshare.com/wiki/Pico-ePaper-7.5-B

# https://github.com/waveshareteam/Pico_ePaper_Code/blob/main/python/Pico-ePaper-7.5-B.py

# text, line, rectangle, circle, ellipse, polygon, arc
# https://docs.micropython.org/en/latest/library/framebuf.html
# lähdekoodi
# https://github.com/micropython/micropython/blob/master/extmod/modframebuf.c

# isompi fontti
# https://github.com/peter-l5/framebuf2

# ääkköset saa toimimaan tällö (ei testattu):
# https://github.com/peterhinch/micropython-font-to-py

# Lataa writer.py ja siirrä se laitteesi muistiin.
# Hanki fontti: Kirjasto vaatii fontin Python-muodossa. Löydät valmiita esimerkkifontteja (sisältäen ääkköset) täältä.
# Käyttö:
# python

# from writer import Writer
# import my_font_file  # Valmiiksi käännetty fonttitiedosto

# # Alustus (fb = sinun framebuf-oliosi)
# wri = Writer(fb, my_font_file)
# wri.set_textpos(0, 0)
# wri.printstring("Ääkköset toimivat!")
# fb.show()


from umqtt.simple import MQTTClient
import ubinascii
import time
import network
# own library
import config
import EPD_7in5_B

print(dir(time))
print(time.ticks_us())

def debug_print(message):
    """Print message if debug is True, otherwise do nothing."""
    if config.DEBUG:
        print(message)

def restart_and_reconnect():
  debug_print('Failed to connect to MQTT broker. Reconnecting...')
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
  debug_print((topic, msg))
  if topic == config.mqtt_topic_outdoor_temperature:
    debug_print('Outdoor temperature received: %s °C' % msg.decode())

def mqtt_connect_and_subscribe():
  client = MQTTClient(config.client_id, config.mqtt_server, user=config.mqtt_user, password=config.mqtt_pass)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(config.mqtt_topic)
  debug_print('Connected to %s MQTT broker, subscribed to %s topic' % (config.mqtt_server, config.mqtt_topic))
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

def init_epd():
    epd = EPD_7in5_B.EPD_7in5_B()
    epd.Clear()

    return epd

def epd_close(epd):
    epd.init()       
    epd.Clear()
    epd.delay_ms(2000)
    debug_print("sleep")
    epd.sleep()
    debug_print("close")

def epd_draw_corners(epd):
    # partial update
    epd.init()
    epd.imageblack.fill(0xff)
    epd.display_Base_color(0xFF)
    epd.init_part()
    for i in range(0, 10):
        epd.imageblack.fill_rect(175, 105, 10, 10, 0xff)
        epd.imageblack.text(str(i), 177, 106, 0x00)
        epd.display_Partial(epd.buffer_black, 0, 0, 800, 480)

if __name__=='__main__':
    try:
        wlan = wlan_connect()
        client = mqtt_connect_and_subscribe()
        epd = init_epd()

        epd.imageblack.fill(0xff)
        epd.imagered.fill(0x00)

        epd.imageblack.text("Ulkolämpötila 15.5", 5, 10, 0x00)
        epd.imagered.text("Sisälämpötila 22.3", 5, 40, 0xff)
        epd.display()
        epd.delay_ms(5000)

        time.sleep(10)
        epd.Clear()
        epd.imageblack.fill(0xff)
        epd.imagered.fill(0x00)

        epd.imageblack.text("Ulkolämpötila 15.5", 5, 10, 0x00)
        epd.imagered.text("Sisälämpötila 11.3", 5, 40, 0xff)
        epd.display()
        epd.delay_ms(5000)
        time.sleep(10)


    except OSError as e:
        epd_close(epd)
        restart_and_reconnect()


    # listen_for_messages(client)

    epd_close(epd)
    restart_and_reconnect()