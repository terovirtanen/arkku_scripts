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


def get_all_prices_for_period(cursor, start_time, end_time):
    """Get all price data points for the specified time period."""
    query = """
    SELECT timestamp, price
    FROM prices 
    WHERE timestamp >= %s AND timestamp < %s
    ORDER BY timestamp
    """
    
    cursor.execute(query, (start_time, end_time))
    results = cursor.fetchall()
    
    print(f"Found {len(results)} price data points in the period")
    return results


def calculate_period_averages(price_data, period_hours=3):
    """Calculate average prices for consecutive 3-hour periods from all available data points."""
    if not price_data:
        return {}
    
    # Group all prices by hour
    hourly_data = {}
    for timestamp, price in price_data:
        # Round down to hour
        hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
        if hour_key not in hourly_data:
            hourly_data[hour_key] = []
        hourly_data[hour_key].append(float(price))
    
    # Calculate hourly averages
    hourly_averages = {}
    for hour, prices in hourly_data.items():
        hourly_averages[hour] = sum(prices) / len(prices)
        print(f"  {hour.strftime('%Y-%m-%d %H:00')}: {len(prices)} data points, avg {hourly_averages[hour]:.2f} c/kWh")
    
    return hourly_averages


def find_cheapest_3h_period(price_data, timezone):
    """Find the cheapest consecutive 3-hour period between 22:00-04:00 (can start at any time)."""
    best_start = None
    best_avg_price = float('inf')
    best_period_prices = []
    
    # Sort all price data by timestamp
    sorted_prices = sorted(price_data, key=lambda x: x[0])
    
    print(f"Analyzing {len(sorted_prices)} price data points for 3-hour windows...")
    
    # Check every possible 3-hour window starting from each data point
    for i, (start_time, _) in enumerate(sorted_prices):
        # Check if this start time is in allowed window (22:00-04:00)
        hour_of_day = start_time.hour
        if not (hour_of_day >= 22 or hour_of_day <= 1):  # Allow starts until 01:xx (ending at 04:xx)
            continue
        
        # Calculate end time for 3-hour window
        end_time = start_time + timedelta(hours=3)
        
        # Collect all prices within this 3-hour window
        window_prices = []
        for timestamp, price in sorted_prices:
            if start_time <= timestamp < end_time:
                window_prices.append((timestamp, float(price)))
        
        # Need at least some data points in the window
        if len(window_prices) < 3:  # At least 3 data points (45 minutes of data)
            continue
        
        # Calculate average price for this window
        avg_price = sum(price for _, price in window_prices) / len(window_prices)
        
        print(f"\nChecking period {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}:")
        print(f"  Data points: {len(window_prices)}")
        print(f"  Price range: {min(price for _, price in window_prices):.2f} - {max(price for _, price in window_prices):.2f} c/kWh")
        print(f"  Average: {avg_price:.2f} c/kWh")
        
        if avg_price < best_avg_price:
            best_avg_price = avg_price
            best_start = start_time
            best_period_prices = window_prices
            print(f"  ⭐ New best period found!")
    
    return best_start, best_avg_price, best_period_prices


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
            # Get all price data points
            price_data = get_all_prices_for_period(cursor, start_time, end_time)
            
            if not price_data:
                print("No price data available for the specified period.")
                return 1
            
            # Find cheapest 3-hour period (can start at any time)
            best_start, best_avg_price, best_period_data = find_cheapest_3h_period(price_data, timezone)
            
            if best_start is None:
                print("No suitable 3-hour period found between 22:00-04:00")
                return 1
            
            print(f"\n🎯 BEST 3-HOUR PERIOD FOUND:")
            print(f"   Start time: {best_start.strftime('%Y-%m-%d %H:%M')}")
            print(f"   End time:   {(best_start + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M')}")
            print(f"   Average price: {best_avg_price:.2f} c/kWh")
            print(f"   Data points in period: {len(best_period_data)}")
            print(f"   Price range: {min(price for _, price in best_period_data):.2f} - {max(price for _, price in best_period_data):.2f} c/kWh")
            
            # Show first and last few data points
            print(f"   Sample data points:")
            sample_data = best_period_data[:3] + (best_period_data[-3:] if len(best_period_data) > 6 else [])
            for timestamp, price in sample_data:
                print(f"     {timestamp.strftime('%H:%M')}: {price:.2f} c/kWh")
            
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