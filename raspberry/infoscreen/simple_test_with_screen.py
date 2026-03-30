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
import ujson
import time
import network
# own library
import config
import EPD_7in5_B
from window_temperature import WindowTemperature

print(dir(time))
print(time.ticks_us())


class WlanConnection:
    def __init__(
        self,
        ssid,
        password,
        debug=False,
        logger=None,
        max_wait=10,
        wait_seconds=2,
    ):
        self.ssid = ssid
        self.password = password
        self.debug = debug
        self.logger = logger
        self.max_wait = max_wait
        self.wait_seconds = wait_seconds
        self.wlan = network.WLAN(network.STA_IF)

    def _log(self, message):
        if self.debug and self.logger is not None:
            self.logger(message)

    def connect(self):
        self.wlan.active(True)

        if self.wlan.status() != 3:
            self.wlan.connect(self.ssid, self.password)

        max_wait = self.max_wait
        while max_wait > 0:
            status = self.wlan.status()
            if status < 0 or status >= 3:
                break

            max_wait -= 1
            self._log('waiting for connection...')
            time.sleep(self.wait_seconds)

        status = self.wlan.status()
        if status != 3:
            raise OSError('network connection failed (status=%s)' % status)

        self._log('network connected')
        return self.wlan

    def disconnect(self):
        self.wlan.disconnect()
        self.wlan.active(False)

    def is_connected(self):
        return self.wlan.status() == 3


class MqttConnection:
    TOPIC_NAMES = {
        config.mqtt_topic_outdoor_temperature: 'outdoor',
        config.mqtt_topic_warehouse_temperature: 'warehouse',
        config.mqtt_topic_garage_temperature: 'garage',
    }

    def __init__(
        self,
        client_id,
        server,
        user=None,
        password=None,
        subscribe_topic=None,
        debug=False,
        logger=None,
    ):
        self.client_id = client_id
        self.server = server
        self.user = user
        self.password = password
        self.subscribe_topic = subscribe_topic
        self.debug = debug
        self.logger = logger
        self.client = MQTTClient(client_id, server, user=user, password=password)
        self.client.set_callback(self._on_message)
        self.messages = {}
        self.changed_messages = {}

    def _log(self, message):
        if self.debug and self.logger is not None:
            self.logger(message)

    def _on_message(self, topic, msg):
        topic_name = self._topic_name(topic)
        value = self._decode_message(msg)
        previous_value = self.messages.get(topic_name)

        self._log((topic_name, value))

        if previous_value != value:
            self.messages[topic_name] = value
            self.changed_messages[topic_name] = value

        if topic == config.mqtt_topic_outdoor_temperature:
            self._log('Outdoor temperature received: %s °C' % value)
        if topic == config.mqtt_topic_warehouse_temperature:
            self._log('Warehouse temperature received: %s °C' % value)
        if topic == config.mqtt_topic_garage_temperature:
            self._log('Garage temperature received: %s °C' % value)

    def _topic_name(self, topic):
        return self.TOPIC_NAMES.get(topic, self._decode_message(topic))

    def _decode_message(self, msg):
        # '{"tC":15.3,"ts":"2026-1-18T17:59:27"}'
        # {'2026-3-30T18:1:25': 2.7}
        try:
            decoded_str = msg.decode()
            data = ujson.loads(decoded_str)
            # config.debug_print('Decoded MQTT message: %s' % data)

            if isinstance(data, dict):
                if 'tC' in data:
                    value = data['tC']
                    # config.debug_print('Decoded MQTT message tC: %s' % value)
                    return value

                if len(data) == 1:
                    for _, value in data.items():
                        if isinstance(value, (int, float)):
                            # config.debug_print('Decoded MQTT message single value: %s' % value)
                            return value

                # config.debug_print('Decoded MQTT message no temperature key, fallback to raw string')
                return decoded_str

            if isinstance(data, (int, float)):
                return data

            return decoded_str
        except (AttributeError, ValueError):
            return msg

    def _fetch_initial_retained(self, duration_ms=2000, poll_sleep_ms=50):
        deadline = time.ticks_add(time.ticks_ms(), duration_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            self.check_msg()
            time.sleep_ms(poll_sleep_ms)

    def connect_and_subscribe(self):
        self.client.connect()
        if self.subscribe_topic is not None:
            self.client.subscribe(self.subscribe_topic)
            self._fetch_initial_retained()
            self._log('Connected to %s MQTT broker, subscribed to %s topic' % (self.server, self.subscribe_topic))
        else:
            self._log('Connected to %s MQTT broker' % self.server)
        return self.client

    def check_msg(self):
        self.client.check_msg()

    def read_changed_messages(self):
        changed_messages = self.changed_messages
        self.changed_messages = {}
        return changed_messages

    def get_message(self, topic, default=None):
        topic_name = self._topic_name(topic) if isinstance(topic, bytes) else topic
        return self.messages.get(topic_name, default)

    def get_current_values(self):
        return {
            'outdoor': self.get_message('outdoor'),
            'warehouse': self.get_message('warehouse'),
            'garage': self.get_message('garage'),
        }

    def disconnect(self):
        self.client.disconnect()

def restart_and_reconnect():
    config.debug_print('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(10)
    machine.soft_reset()

def sleep_or_deepsleep(duration_ms):
    """Sleep for duration_ms milliseconds. Uses sleep if debug=True, otherwise deepsleep."""
    if config.DEBUG:
        time.sleep(duration_ms / 1000)
    else:
        # f.write(str(duration_ms) + "\n")
        # f.close()
        # deepsleep ei toimi, ei odota vaan tekee resetin heti
        # machine.deepsleep(duration_ms)
        time.sleep(duration_ms / 1000)
        machine.soft_reset()

def wlan_connect():
    wlan_connection = WlanConnection(
        config.WLAN_SSID,
        config.WLAN_PASSWORD,
        debug=config.DEBUG,
        logger=config.debug_print,
    )

    try:
        return wlan_connection.connect()
    except OSError as error:
        config.debug_print(str(error))
        sleep_or_deepsleep(30000) # sleep 30 seconds before retry
        raise


def mqtt_connect_and_subscribe():
    mqtt_connection = MqttConnection(
        config.client_id,
        config.mqtt_server,
        user=config.mqtt_user,
        password=config.mqtt_pass,
        subscribe_topic=config.mqtt_topic,
        debug=config.DEBUG,
        logger=config.debug_print,
    )
    mqtt_connection.connect_and_subscribe()
    return mqtt_connection

def listen_for_messages(client, win_temp=None):
    try:
        # Fetch all initial values
        current_values = client.get_current_values()
        outdoor = current_values['outdoor']
        warehouse = current_values['warehouse']
        garage = current_values['garage']
        
        config.debug_print('Initial values: outdoor=%s, warehouse=%s, garage=%s' % (outdoor, warehouse, garage))
        if win_temp is not None:
            if outdoor is not None:
                win_temp.update_outdoor_temperature(outdoor)
            if warehouse is not None:
                win_temp.update_outbuilding_temperature(warehouse)
            if garage is not None:
                win_temp.update_garage_temperature(garage)
        
        # Listen for further changed values
        for _ in range(5):
            client.check_msg()
            changed_messages = client.read_changed_messages()
            if changed_messages:
                config.debug_print('Changed MQTT values: %s' % changed_messages)
                if win_temp is not None:
                    if 'outdoor' in changed_messages:
                        win_temp.update_outdoor_temperature(changed_messages['outdoor'])
                    if 'warehouse' in changed_messages:
                        win_temp.update_outbuilding_temperature(changed_messages['warehouse'])
                    if 'garage' in changed_messages:
                        win_temp.update_garage_temperature(changed_messages['garage'])
            time.sleep(10)
    finally:
        client.disconnect()

def init_epd():
    epd = EPD_7in5_B.EPD_7in5_B()
    epd.init()       
    epd.Clear()

    return epd

def epd_close(epd):
    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    config.debug_print("sleep")
    epd.sleep()
    config.debug_print("close")

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
        mqtt = mqtt_connect_and_subscribe()
        epd = init_epd()

        epd.imageblack.fill(0xff)
        epd.imagered.fill(0x00)

        win_temp = WindowTemperature(epd)

        # epd.imageblack.text("Ulkolämpötila 15.5", 5, 10, 0x00)
        # epd.imagered.text("Sisälämpötila 22.3", 5, 40, 0xff)
        epd.display()
        # epd.delay_ms(5000)

        # win_temp.update_outdoor_temperature(15.5)
        # epd.delay_ms(3000)
        # win_temp.update_garage_temperature(10.2)
        # epd.delay_ms(3000)

        # time.sleep(10)
        # epd.Clear()
        # epd.imageblack.fill(0xff)
        # epd.imagered.fill(0x00)

        # epd.imageblack.text("Ulkolämpötila 15.5", 5, 10, 0x00)
        # epd.imagered.text("Sisälämpötila 11.3", 5, 40, 0xff)
        # epd.display()
        # epd.delay_ms(5000)
        # time.sleep(10)

        listen_for_messages(mqtt, win_temp)

    except OSError as e:
        epd_close(epd)
        restart_and_reconnect()



    epd_close(epd)
    # restart_and_reconnect()