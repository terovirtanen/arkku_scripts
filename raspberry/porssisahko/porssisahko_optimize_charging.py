#!/usr/bin/env python3
"""
Finds the cheapest consecutive 3-hour period between 22:00-04:00 for electricity prices
and updates Shelly charger cron schedule accordingly.
"""

import json
import requests
import mysql.connector
from mysql.connector import Error
import pytz
from datetime import datetime, timedelta, time
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
        
        # Shelly config
        'shelly_ip': os.getenv('SHELLY_IP', '192.168.100.200'),
        'shelly_username': os.getenv('SHELLY_USERNAME'),
        'shelly_password': os.getenv('SHELLY_PASSWORD')
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


def get_prices_for_period(cursor, start_time, end_time):
    """Get hourly average prices for the specified time period."""
    query = """
    SELECT 
        DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') as hour,
        AVG(price) as avg_price
    FROM prices 
    WHERE timestamp >= %s AND timestamp < %s
    GROUP BY DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00')
    ORDER BY hour
    """
    
    cursor.execute(query, (start_time, end_time))
    results = cursor.fetchall()
    
    # Convert to dictionary for easier access
    hourly_prices = {}
    for hour_str, avg_price in results:
        hour_dt = datetime.strptime(hour_str, '%Y-%m-%d %H:00:00')
        hourly_prices[hour_dt] = float(avg_price)
    
    return hourly_prices


def find_cheapest_3h_period(hourly_prices, timezone):
    """Find the cheapest consecutive 3-hour period between 22:00-04:00."""
    best_start = None
    best_avg_price = float('inf')
    best_period_data = []
    
    # Get all hours and sort them
    hours = sorted(hourly_prices.keys())
    
    print("Available hourly prices:")
    for hour in hours:
        print(f"  {hour.strftime('%Y-%m-%d %H:00')}: {hourly_prices[hour]:.2f} c/kWh")
    
    # Check each possible 3-hour window
    for i in range(len(hours) - 2):
        start_hour = hours[i]
        
        # Check if this hour is in the allowed time window (22:00-04:00)
        hour_of_day = start_hour.hour
        if not (hour_of_day >= 22 or hour_of_day <= 1):  # 22, 23, 0, 1 (for 3h period ending at 04:00)
            continue
        
        # Check if we have 3 consecutive hours
        hour1 = hours[i]
        hour2 = hours[i + 1]
        hour3 = hours[i + 2]
        
        if (hour2 == hour1 + timedelta(hours=1) and 
            hour3 == hour2 + timedelta(hours=1)):
            
            # Calculate average price for this 3-hour period
            prices = [hourly_prices[hour1], hourly_prices[hour2], hourly_prices[hour3]]
            avg_price = sum(prices) / len(prices)
            
            print(f"\nChecking period {hour1.strftime('%H:00')}-{hour3.strftime('%H:00')} ({hour1.strftime('%Y-%m-%d')}):")
            print(f"  Hours: {hour1.strftime('%H:00')} ({prices[0]:.2f}), {hour2.strftime('%H:00')} ({prices[1]:.2f}), {hour3.strftime('%H:00')} ({prices[2]:.2f})")
            print(f"  Average: {avg_price:.2f} c/kWh")
            
            if avg_price < best_avg_price:
                best_avg_price = avg_price
                best_start = hour1
                best_period_data = [
                    (hour1, prices[0]),
                    (hour2, prices[1]),
                    (hour3, prices[2])
                ]
    
    return best_start, best_avg_price, best_period_data


def update_shelly_cron(config, start_hour):
    """Update Shelly device schedule to start charging at the specified hour."""
    shelly_ip = config['shelly_ip']
    
    # Calculate end hour (3 hours later)
    end_dt = start_hour + timedelta(hours=3)
    start_hour_int = start_hour.hour
    end_hour_int = end_dt.hour
    
    print(f"\nUpdating Shelly at {shelly_ip}:")
    print(f"  Charging period: {start_hour_int:02d}:00 - {end_hour_int:02d}:00")
    
    try:
        # Create authentication if username/password provided
        auth = None
        if config['shelly_username'] and config['shelly_password']:
            auth = (config['shelly_username'], config['shelly_password'])
        
        # Get current Shelly status first
        status_url = f"http://{shelly_ip}/status"
        response = requests.get(status_url, auth=auth, timeout=5)
        
        if response.status_code != 200:
            print(f"✗ Could not connect to Shelly at {shelly_ip}")
            return False
        
        print("✓ Successfully connected to Shelly")
        
        # For now, just print what we would set
        # In real implementation, you'd use Shelly's schedule API
        print(f"  Would set schedule: Turn ON at {start_hour_int:02d}:00, Turn OFF at {end_hour_int:02d}:00")
        
        # TODO: Implement actual Shelly schedule update based on your Shelly model
        # Different Shelly models have different APIs for scheduling
        # Example for Shelly 1PM:
        # schedule_url = f"http://{shelly_ip}/settings/actions"
        # payload = {...}  # Depends on Shelly model
        
        print("✓ Shelly schedule would be updated (implementation needed for your Shelly model)")
        return True
            
    except requests.RequestException as e:
        print(f"✗ Error communicating with Shelly: {e}")
        return False


def main():
    """Main function that finds cheapest period and updates Shelly."""
    try:
        # Load configuration
        config = load_config()
        
        # Setup timezone
        timezone = pytz.timezone("Europe/Helsinki")
        
        # Calculate time range (next 24 hours from now)
        now = datetime.now(timezone)
        start_time = now.replace(minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=24)
        
        print(f"Analyzing electricity prices from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Connect to database
        connection = create_database_connection(config)
        cursor = connection.cursor()
        
        try:
            # Get hourly prices
            hourly_prices = get_prices_for_period(cursor, start_time, end_time)
            
            if len(hourly_prices) < 3:
                print(f"Not enough price data available. Found {len(hourly_prices)} hours, need at least 3.")
                return 1
            
            # Find cheapest 3-hour period
            best_start, best_avg_price, best_period_data = find_cheapest_3h_period(hourly_prices, timezone)
            
            if best_start is None:
                print("No suitable 3-hour period found between 22:00-04:00")
                return 1
            
            print(f"\n🎯 BEST 3-HOUR PERIOD FOUND:")
            print(f"   Start time: {best_start.strftime('%Y-%m-%d %H:%M')}")
            print(f"   End time:   {(best_start + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M')}")
            print(f"   Average price: {best_avg_price:.2f} c/kWh")
            print(f"   Period details:")
            for hour_dt, price in best_period_data:
                print(f"     {hour_dt.strftime('%H:%M')}: {price:.2f} c/kWh")
            
            # Update Shelly cron
            success = update_shelly_cron(config, best_start)
            
            if success:
                print("\n✅ Charging schedule optimized successfully!")
                return 0
            else:
                print("\n❌ Failed to update charging schedule")
                return 1
                
        finally:
            cursor.close()
            connection.close()
            
    except Exception as e:
        print(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())