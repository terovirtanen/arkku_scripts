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

# Display resolution
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

DEBUG = True


def debug_print(message):
	if DEBUG:
		print(message)
