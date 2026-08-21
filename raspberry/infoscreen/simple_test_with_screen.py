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
import ntptime
import ubinascii
import ujson
import time
import network
# own library
import config
import EPD_7in5_B

from window_heating import WindowHeating
from window_spot_prices import WindowSpotPrices
from window_temperature import WindowTemperature
from window_carcharger import WindowCarCharger

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

        self._log('connect to %s with %s' % (self.ssid, self.password))

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
        config.mqtt_topic_heating_tank_down_temperature: 'heating_tank_down',
        config.mqtt_topic_heating_tank_up_temperature: 'heating_tank_up',
        config.mqtt_topic_heating_tank_resistance_running: 'heating_tank_resistance_running',
        config.mqtt_topic_heating_boiler_temperature: 'heating_boiler_temperature',
        config.mqtt_topic_heating_boiler_running: 'heating_boiler_running',
        config.mqtt_topic_spot_prices_long: 'spot_prices_long',
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
        if topic == config.mqtt_topic_heating_tank_down_temperature:
            self._log('Heating tank down temperature received: %s °C' % value)
        if topic == config.mqtt_topic_heating_tank_up_temperature:
            self._log('Heating tank up temperature received: %s °C' % value)
        if topic == config.mqtt_topic_heating_tank_resistance_running:
            self._log('Heating tank resistance running received: %s' % value)
        if topic == config.mqtt_topic_heating_boiler_temperature:
            self._log('Heating boiler temperature received: %s °C' % value)
        if topic == config.mqtt_topic_heating_boiler_running:
            self._log('Heating boiler running received: %s' % value)
        if topic == config.mqtt_topic_spot_prices_long:
            self._log('Spot prices received')

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
                        if isinstance(value, (int, float, bool)):
                            # config.debug_print('Decoded MQTT message single value: %s' % value)
                            return value

                return data

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
            'heating_tank_down': self.get_message('heating_tank_down'),
            'heating_tank_up': self.get_message('heating_tank_up'),
            'heating_tank_resistance_running': self.get_message('heating_tank_resistance_running', False),
            'heating_boiler_temperature': self.get_message('heating_boiler_temperature'),
            'heating_boiler_running': self.get_message('heating_boiler_running', False),
            'spot_prices_long': self.get_message('spot_prices_long'),
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


def sync_time_with_ntp():
    try:
        config.debug_print('Syncing RTC with NTP')
        ntptime.settime()
        config.debug_print('RTC synced: %s' % (time.localtime(),))
    except OSError as error:
        config.debug_print('NTP sync failed: %s' % error)


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


def _parse_spot_day_key(day_key):
    parts = day_key.split('-')
    if len(parts) != 3:
        raise ValueError('Invalid day key: %s' % day_key)
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def _parse_spot_timestamp_key(timestamp_key):
    date_and_time = timestamp_key.split('T')
    if len(date_and_time) != 2:
        raise ValueError('Invalid timestamp key: %s' % timestamp_key)

    year, month, day = _parse_spot_day_key(date_and_time[0])

    time_parts = date_and_time[1].split(':')
    if len(time_parts) < 2:
        raise ValueError('Invalid timestamp key: %s' % timestamp_key)

    hour = int(time_parts[0])
    minute = int(time_parts[1])
    quarter = minute // 15
    if quarter > 3:
        quarter = 3

    return (year, month, day, hour, quarter)


def _build_spot_price_points(spot_prices_long):
    if not isinstance(spot_prices_long, dict):
        return []

    points = []
    for day_key, hours in spot_prices_long.items():
        # Support flat format, e.g. {'2026-3-30T18:1:25': 2.7}
        if isinstance(hours, (int, float)):
            try:
                year, month, day, hour, quarter = _parse_spot_timestamp_key(day_key)
            except ValueError:
                continue

            points.append((year, month, day, hour, quarter, hours))
            continue

        try:
            year, month, day = _parse_spot_day_key(day_key)
        except ValueError:
            continue

        if not isinstance(hours, dict):
            continue

        for hour_key, quarters in hours.items():
            try:
                hour = int(hour_key)
            except ValueError:
                continue

            if not isinstance(quarters, list):
                continue

            for quarter, value in enumerate(quarters):
                if quarter > 3:
                    break
                if isinstance(value, (int, float)):
                    points.append((year, month, day, hour, quarter, value))

    points.sort()
    return points

# ('spot_prices_long', {'2026-4-5': {'22': [0, 0, 0, 0], '23': [0, 0, 0, 0], '18': [0, 0, 0, 0], '19': [0, 1, 1, 0], '21': [0, 1, 0, 0], '20': [1, 1, 1, 1]}})
def _resolve_spot_prices(spot_prices_long):
    points = _build_spot_price_points(spot_prices_long)
    if not points:
        return (None, [])

    now = time.localtime()
    current_marker = (now[0], now[1], now[2], now[3], now[4] // 15)

    current_price = None
    future_points = []
    for year, month, day, hour, quarter, value in points:
        marker = (year, month, day, hour, quarter)
        if marker == current_marker and current_price is None:
            current_price = value
        if marker >= current_marker:
            future_points.append((hour, quarter, value))

    if current_price is None:
        if future_points:
            current_price = future_points[0][2]
        else:
            current_price = points[-1][5]

    return (current_price, future_points)

def init_windows_from_mqtt(client, win_temp=None, win_heating=None, win_spot_prices=None):
    current_values = client.get_current_values()
    outdoor = current_values['outdoor']
    warehouse = current_values['warehouse']
    garage = current_values['garage']
    heating_tank_down = current_values['heating_tank_down']
    heating_tank_up = current_values['heating_tank_up']
    heating_tank_resistance_running = current_values['heating_tank_resistance_running']
    heating_boiler_temperature = current_values['heating_boiler_temperature']
    heating_boiler_running = current_values['heating_boiler_running']
    spot_prices_long = current_values['spot_prices_long']
    current_spot_price, future_spot_prices = _resolve_spot_prices(spot_prices_long)

    config.debug_print(
        'Initial values: outdoor=%s, warehouse=%s, garage=%s, tank_down=%s, tank_up=%s, tank_resistance_running=%s, boiler_temperature=%s, boiler_running=%s, current_spot_price=%s'
        % (
            outdoor,
            warehouse,
            garage,
            heating_tank_down,
            heating_tank_up,
            heating_tank_resistance_running,
            heating_boiler_temperature,
            heating_boiler_running,
            current_spot_price,
        )
    )
    if win_temp is not None:
        if outdoor is not None:
            win_temp.update_outdoor_temperature(outdoor, refresh=False)
        if warehouse is not None:
            win_temp.update_outbuilding_temperature(warehouse, refresh=False)
        if garage is not None:
            win_temp.update_garage_temperature(garage, refresh=False)
    if win_heating is not None:
        win_heating.update_values(
            tank_down_temperature=heating_tank_down,
            tank_up_temperature=heating_tank_up,
            tank_resistance_running=heating_tank_resistance_running,
            boiler_temperature=heating_boiler_temperature,
            boiler_running=heating_boiler_running,
            refresh=False,
        )
    if win_spot_prices is not None:
        win_spot_prices.update_prices(current_spot_price, future_spot_prices, refresh=False)


def listen_for_messages(client, win_temp=None, win_heating=None, win_spot_prices=None, loops = 5, sleeptime_seconds = 10):
    
    # try:
        # Listen for further changed values
        for _ in range(loops):
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
                if win_heating is not None:
                    if 'heating_tank_down' in changed_messages:
                        win_heating.update_tank_down_temperature(changed_messages['heating_tank_down'])
                    if 'heating_tank_up' in changed_messages:
                        win_heating.update_tank_up_temperature(changed_messages['heating_tank_up'])
                    if 'heating_tank_resistance_running' in changed_messages:
                        win_heating.update_tank_resistance_running(changed_messages['heating_tank_resistance_running'])
                    if 'heating_boiler_temperature' in changed_messages:
                        win_heating.update_boiler_temperature(changed_messages['heating_boiler_temperature'])
                    if 'heating_boiler_running' in changed_messages:
                        win_heating.update_boiler_running(changed_messages['heating_boiler_running'])
                if win_spot_prices is not None and 'spot_prices_long' in changed_messages:
                    current_spot_price, future_spot_prices = _resolve_spot_prices(changed_messages['spot_prices_long'])
                    win_spot_prices.update_prices(current_spot_price, future_spot_prices)
            time.sleep(sleeptime_seconds)
    # finally:
    #     client.disconnect()

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


def testing_windows(client, win_temp=None, win_heating=None, win_spot_prices=None):
    config.debug_print('testing_windows')
    if win_temp is not None:
        win_temp.update_outdoor_temperature("eka")
        time.sleep(10)

        win_temp.update_outbuilding_temperature("toka")
        time.sleep(10)

        win_temp.update_outdoor_temperature("eka2")
        time.sleep(10)

        win_temp.update_garage_temperature("kolmas")
        time.sleep(10)

    if win_heating is not None:
        time.sleep(10)
        win_heating.update_tank_down_temperature("neljas")
        time.sleep(10)
        win_heating.update_tank_up_temperature("viides")
        time.sleep(10)
        win_heating.update_tank_resistance_running("kuudes")
        time.sleep(10)
        win_heating.update_boiler_temperature("seitsemäs")
        time.sleep(10)
        win_heating.update_boiler_running("kahdeksas")
        time.sleep(10)
    if win_spot_prices is not None:
        time.sleep(10)
        current_spot_price, future_spot_prices = _resolve_spot_prices("yhdeksäs")
        win_spot_prices.update_prices(-2.34, future_spot_prices)


if __name__=='__main__':
    try:
        wlan = wlan_connect()
        sync_time_with_ntp()
        mqtt = mqtt_connect_and_subscribe()
        epd = init_epd()

        epd.imageblack.fill(0xff)
        epd.imagered.fill(0x00)


        win_temp = WindowTemperature(epd)
        win_heating = WindowHeating(epd)
        win_spot_prices = WindowSpotPrices(epd)
        win_carcharger = WindowCarCharger(epd)


        init_windows_from_mqtt(mqtt, win_temp, win_heating, win_spot_prices)


        epd.blit(win_temp.imageblack, win_temp.imagered, win_temp.Xstart, win_temp.Ystart)
        epd.blit(win_heating.imageblack, win_heating.imagered, win_heating.Xstart, win_heating.Ystart)
        epd.blit(win_spot_prices.imageblack, win_spot_prices.imagered, win_spot_prices.Xstart, win_spot_prices.Ystart)
        epd.blit(win_carcharger.imageblack, win_carcharger.imagered, win_carcharger.Xstart, win_carcharger.Ystart)

        # epd.imageblack.text("Ulkolämpötila 15.5", 5, 10, 0x00)
        # epd.imagered.text("Sisälämpötila 22.3", 5, 40, 0xff)
        epd.display()
        # epd.delay_ms(5000)
        epd.init_part()

        # testing windows
        # if config.DEBUG:
        #     testing_windows(mqtt, win_temp, win_heating, win_spot_prices)
        #     listen_for_messages(mqtt, win_temp, win_heating, win_spot_prices)
        #     epd.init_Fast()
        #     epd.display()
        #     # listen_for_mess
        #     time.sleep(10)
        #     epd.init_Fast()
        #     epd.display()
        #     time.sleep(10)
        # else:

        # prod vals
        for _ in range(6):
            listen_for_messages(mqtt, win_temp, win_heating, win_spot_prices, 20, 30)
            epd.init_Fast()
            epd.display()
            time.sleep(10)
        

    except OSError as e:
        mqtt.disconnect()
        epd_close(epd)
        restart_and_reconnect()

    # if config.DEBUG:
    #     epd_close(epd)
    # else:
    #     restart_and_reconnect()
    mqtt.disconnect()
    epd_close(epd)
