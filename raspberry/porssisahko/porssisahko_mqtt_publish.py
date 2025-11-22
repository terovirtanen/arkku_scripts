#!/usr/bin/env python3
"""
Reads electricity price data from MySQL database and publishes to MQTT broker.
Sends last 2 hours of price data in the format expected by Shelly devices.
"""

import json
import mysql.connector
from mysql.connector import Error
import paho.mqtt.client as mqtt
import pytz
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv


def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    
    config = {
        # Database config
        'db_host': os.getenv('DB_HOST', 'localhost'),
        'db_port': int(os.getenv('DB_PORT', 3306)),
        'db_username': os.getenv('DB_USERNAME'),
        'db_password': os.getenv('DB_PASSWORD'),
        
        # MQTT config
        'mqtt_host': os.getenv('MQTT_HOST', 'localhost'),
        'mqtt_port': int(os.getenv('MQTT_PORT', 1883)),
        'mqtt_username': os.getenv('MQTT_USERNAME'),
        'mqtt_password': os.getenv('MQTT_PASSWORD'),
        'mqtt_topic': os.getenv('MQTT_TOPIC', 'porssisahko/prices'),
        'mqtt_client_id': os.getenv('MQTT_CLIENT_ID', 'porssisahko_publisher')
    }
    
    if not config['db_username'] or not config['db_password']:
        raise ValueError("DB_USERNAME and DB_PASSWORD must be set in .env file")
    
    return config


def create_database_connection(config):
    """Create MySQL database connection."""
    try:
        connection = mysql.connector.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_username'],
            password=config['db_password'],
            database='porssisahkonet',
            charset='utf8mb4'
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        raise


def get_price_data(cursor, hours_back=2):
    """Get price data from database for the last N hours."""
    timezone = pytz.timezone("Europe/Helsinki")
    now = datetime.now(timezone)
    
    # Calculate time range for last N hours
    start_time = now - timedelta(hours=hours_back)
    
    query = """
    SELECT timestamp, price 
    FROM prices 
    WHERE timestamp >= %s AND timestamp <= %s
    ORDER BY timestamp ASC
    """
    
    cursor.execute(query, (start_time, now))
    return cursor.fetchall()


def format_price_data(price_data, timezone):
    """Format price data to match Shelly expected format."""
    formatted_data = {}
    
    for timestamp, price in price_data:
        # Convert to timezone-aware datetime if needed
        if timestamp.tzinfo is None:
            timestamp = timezone.localize(timestamp)
        else:
            timestamp = timestamp.astimezone(timezone)
        
        # Format date as "YYYY-M-D" (no leading zeros)
        date_key = timestamp.strftime("%Y-%-m-%-d")
        hour = timestamp.hour
        minute = timestamp.minute
        quarter = minute // 15  # Quarter-hour index (0-3)
        price_int = int(price)  # Convert to integer as in original PHP
        
        if date_key not in formatted_data:
            formatted_data[date_key] = {}
        
        if hour not in formatted_data[date_key]:
            # Initialize array with 4 null values
            formatted_data[date_key][hour] = [None] * 4
        
        formatted_data[date_key][hour][quarter] = price_int
    
    return formatted_data


def publish_to_mqtt(config, data):
    """Publish data to MQTT broker."""
    client = mqtt.Client(client_id=config['mqtt_client_id'])
    
    # Set username and password if provided
    if config['mqtt_username'] and config['mqtt_password']:
        client.username_pw_set(config['mqtt_username'], config['mqtt_password'])
    
    try:
        # Connect to MQTT broker
        client.connect(config['mqtt_host'], config['mqtt_port'], 60)
        
        # Publish data
        json_data = json.dumps(data)
        result = client.publish(config['mqtt_topic'], json_data, qos=1, retain=True)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Successfully published to MQTT topic: {config['mqtt_topic']}")
            print(f"Data size: {len(json_data)} bytes")
            return True
        else:
            print(f"Failed to publish to MQTT: {result.rc}")
            return False
            
    except Exception as e:
        print(f"MQTT error: {e}")
        return False
    finally:
        client.disconnect()


def main():
    """Main function that reads price data and publishes to MQTT."""
    try:
        # Load configuration
        config = load_config()
        
        # Setup timezone
        timezone = pytz.timezone("Europe/Helsinki")
        
        # Connect to database
        connection = create_database_connection(config)
        cursor = connection.cursor()
        
        try:
            # Get price data for last 2 hours
            price_data = get_price_data(cursor, hours_back=2)
            
            if not price_data:
                print("No price data found for the last 2 hours")
                return 1
            
            print(f"Retrieved {len(price_data)} price records from database")
            
            # Format data
            formatted_data = format_price_data(price_data, timezone)
            
            if not formatted_data:
                print("No formatted data to publish")
                return 1
            
            # Publish to MQTT
            success = publish_to_mqtt(config, formatted_data)
            
            if success:
                print("Price data published successfully")
                # Print sample of published data
                print("Published data sample:")
                print(json.dumps(formatted_data, indent=2)[:500] + "...")
                return 0
            else:
                print("Failed to publish price data")
                return 1
                
        finally:
            cursor.close()
            connection.close()
            
    except Exception as e:
        print(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())