"""
WiFi Configuration
"""

# WiFi credentials
WLAN_SSID = 'your_wifi_ssid'
WLAN_PASSWORD = 'your_wifi_password'

# mqtt
client_id = f'raspberry-infoscreen'
mqtt_server = 'REPLACE_WITH_YOUR_MQTT_BROKER_IP'
mqtt_port = 1883
mqtt_user = 'REPLACE_WITH_YOUR_MQTT_USERNAME'
mqtt_pass = 'REPLACE_WITH_YOUR_MQTT_PASSWORD'
mqtt_topic = b"#"
mqtt_topic_outdoor_temperature = b"outdoor/temperature"
mqtt_topic_warehouse_temperature = b"warehouse/temperature"
mqtt_topic_garage_temperature = b"garage/temperature"

# tulossa lämmitys
# WindowHeating
# heating/tank/up/temperature {"2026-4-1T21:31:9":69.3}
# heating/tank/resistance/running false
# heating/tank/down/temperature {"2026-4-1T21:29:57":65.6}
# heating/boiler/temperature {"2026-4-1T21:29:57":66.6}
# heating/boiler/running false
mqtt_topic_heating_tank_down_temperature = b"heating/tank/down/temperature"
mqtt_topic_heating_tank_up_temperature = b"heating/tank/up/temperature"
mqtt_topic_heating_tank_resistance_running = b"heating/tank/resistance/running"
mqtt_topic_heating_boiler_temperature = b"heating/boiler/temperature"
mqtt_topic_heating_boiler_running = b"heating/boiler/running"

# tulossa porssisahko
# WindowSpotPrices
# porssisahko/prices/long {"2026-4-1": {"21": [1, 1, 1, 1], "22": [1, 1, 1, 1], "23": [1, 1, 1, 1]}, "2026-4-2": {"0": [1, 1, 1, 2], "1": [1, 1, 2, 2], "2": [2, 3, 3, 3]}}
mqtt_topic_spot_prices_long = b"porssisahko/prices/long"
# mqtt_topic_spot_prices_short = b"porssisahko/prices/short"

# Display resolution
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

DEBUG = True


def debug_print(message):
	if DEBUG:
		print(message)
