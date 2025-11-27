#!/usr/bin/env python3
"""
Car Charger Manager Script for Shelly device control.

This script runs every 10 minutes via cron to:
1. Check car_charger table for current and next 30min charging periods
2. Query Shelly device current state
3. Turn charging on/off based on schedule
"""

import json
import mysql.connector
from mysql.connector import Error
import pytz
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv
import sys


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
        'shelly_user': os.getenv('SHELLY_USER', ''),
        'shelly_password': os.getenv('SHELLY_PASSWORD', ''),
        'shelly_enum_id': int(os.getenv('SHELLY_ENUM_ID', 200)),  # Default enum ID 200
        'charging_current': int(os.getenv('CHARGING_CURRENT', 16))  # Default 16A (max current)
    }
    
    required_fields = ['db_username', 'db_password']
    missing_fields = [field for field in required_fields if not config[field]]
    
    if missing_fields:
        raise ValueError(f"Required environment variables missing: {', '.join(missing_fields.upper())}")
    
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


def should_charge_now(cursor, current_time):
    """Check if charging should be active during current time + next 30 minutes."""
    # Check time window: now to now + 30 minutes
    end_time = current_time + timedelta(minutes=30)
    
    query = """
    SELECT start_time, end_time, period_type, average_price
    FROM car_charger 
    WHERE (
        (start_time <= %s AND end_time > %s) OR
        (start_time < %s AND end_time >= %s) OR
        (start_time >= %s AND start_time < %s)
    )
    ORDER BY start_time
    """
    
    cursor.execute(query, (
        current_time, current_time,  # Period that covers current time
        end_time, end_time,          # Period that covers end time  
        current_time, end_time       # Period that starts within window
    ))
    
    results = cursor.fetchall()
    
    if results:
        print(f"Found {len(results)} charging periods overlapping with current window:")
        for start_time, end_time, period_type, avg_price in results:
            print(f"  {period_type}: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} (avg: {avg_price:.2f} c/kWh)")
        return True
    else:
        print("No charging periods found for current window")
        return False


def get_shelly_status(config):
    """Get current Shelly charger status, charging state and current."""
    try:
        base_url = f"http://{config['shelly_ip']}/rpc"
        auth = None
        if config['shelly_user'] and config['shelly_password']:
            auth = (config['shelly_user'], config['shelly_password'])
        
        # Get charger status (enum)
        status_url = f"{base_url}/Enum.GetStatus?id={config['shelly_enum_id']}"
        status_response = requests.get(status_url, auth=auth, timeout=10)
        status_response.raise_for_status()
        status_data = status_response.json()
        status_value = status_data.get('value', 'unknown')
        
        # Get charging enabled/disabled state (boolean)
        enabled_url = f"{base_url}/Boolean.GetStatus?id=200"
        enabled_response = requests.get(enabled_url, auth=auth, timeout=10)
        enabled_response.raise_for_status()
        enabled_data = enabled_response.json()
        is_enabled = enabled_data.get('value', False)
        
        # Get current charging current (number)
        current_url = f"{base_url}/Number.GetStatus?id=200"
        current_response = requests.get(current_url, auth=auth, timeout=10)
        current_response.raise_for_status()
        current_data = current_response.json()
        charging_current = current_data.get('value', 0)
        
        print(f"Shelly charger status: {status_value}")
        print(f"Charging enabled: {is_enabled}")
        print(f"Charging current: {charging_current}A")
        
        # Determine if charger is actively charging
        is_charging = (status_value == 'charger_charging') and is_enabled
        
        return is_charging, status_value, is_enabled, charging_current
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting Shelly status: {e}")
        raise
    except (KeyError, ValueError) as e:
        print(f"Error parsing Shelly response: {e}")
        raise


def set_charging_current(config, current_amps):
    """Set charging current for Shelly charger."""
    try:
        base_url = f"http://{config['shelly_ip']}/rpc"
        auth = None
        if config['shelly_user'] and config['shelly_password']:
            auth = (config['shelly_user'], config['shelly_password'])
        
        # Set charging current via Number.Set
        url = f"{base_url}/Number.Set"
        payload = {
            "id": 200,
            "value": current_amps
        }
        
        response = requests.post(url, auth=auth, timeout=10, json=payload)
        response.raise_for_status()
        
        print(f"✓ Charging current set to {current_amps}A")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error setting charging current: {e}")
        return False
    except (KeyError, ValueError) as e:
        print(f"Error parsing response: {e}")
        return False


def set_shelly_charging_state(config, enable_charging, current_amps=None):
    """Enable or disable Shelly charger with optional current setting."""
    try:
        base_url = f"http://{config['shelly_ip']}/rpc"
        auth = None
        if config['shelly_user'] and config['shelly_password']:
            auth = (config['shelly_user'], config['shelly_password'])
        
        # Set charging enabled/disabled via Boolean.Set
        action = "enable" if enable_charging else "disable"
        bool_url = f"{base_url}/Boolean.Set"
        bool_payload = {
            "id": 200,
            "value": enable_charging
        }
        
        response = requests.post(bool_url, auth=auth, timeout=10, json=bool_payload)
        response.raise_for_status()
        
        print(f"✓ Shelly charger {action.upper()} command sent")
        
        # If enabling charging, also set the charging current
        if enable_charging and current_amps is not None:
            current_url = f"{base_url}/Number.Set"
            current_payload = {
                "id": 200,
                "value": current_amps
            }
            
            current_response = requests.post(current_url, auth=auth, timeout=10, json=current_payload)
            current_response.raise_for_status()
            
            print(f"✓ Charging current set to {current_amps}A")
        
        # Verify new status after short delay
        import time
        time.sleep(2)
        is_charging, status_value, is_enabled, current = get_shelly_status(config)
        print(f"✓ Charger status after command: enabled={is_enabled}, status={status_value}, current={current}A")
        
        return is_charging
        
    except requests.exceptions.RequestException as e:
        print(f"Error setting Shelly charging state: {e}")
        print(f"⚠️  Command may have failed")
        # Return current state as fallback
        try:
            is_charging, _, _, _ = get_shelly_status(config)
            return is_charging
        except:
            return False
    except (KeyError, ValueError) as e:
        print(f"Error parsing Shelly response: {e}")
        raise


def main():
    """Main function that manages car charger based on schedule and current status.
    
    Logic:
    1. If charger_charging: Check if still allowed, stop if not, adjust current if needed
    2. If charger_end: Check if should restart in next 30min, start with appropriate current
    3. Other status: Start charging if allowed and car is available
    
    Current settings: Day (08:00-23:00) = 16A, Night (23:00-08:00) = 12A
    """
    try:
        # Load configuration
        config = load_config()
        
        # Setup timezone
        timezone = pytz.timezone("Europe/Helsinki")
        current_time = datetime.now(timezone)
        
        print(f"=== Car Charger Manager - {current_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        
        # Connect to database
        connection = create_database_connection(config)
        cursor = connection.cursor()
        
        try:
            # Get current Shelly status first
            is_currently_charging, current_status, is_enabled, charging_current = get_shelly_status(config)
            
            # Check if charging is allowed in next 30 minutes
            should_charge = should_charge_now(cursor, current_time)
            print(f"Charging allowed in next 30min: {'YES' if should_charge else 'NO'}")
            
            # Determine if it's day time (08:00-23:00) or night time
            hour = current_time.hour
            is_day_time = 8 <= hour < 23
            target_current = 16 if is_day_time else 12
            time_period = "DAY" if is_day_time else "NIGHT"
            
            print(f"Current time period: {time_period} (target current: {target_current}A)")
            
            # Decision logic based on charger status
            if current_status == 'charger_charging':
                print("🔍 Charger is currently charging - checking if allowed")
                if not should_charge:
                    print("🛑 Charging not allowed at this time - stopping charger")
                    set_shelly_charging_state(config, False, 0)
                    print("✅ Charging stopped")
                else:
                    # Check if current needs adjustment
                    if charging_current != target_current:
                        print(f"🔧 Adjusting charging current from {charging_current}A to {target_current}A")
                        set_charging_current(config, target_current)
                        print(f"✅ Charging current adjusted to {target_current}A")
                    else:
                        print(f"ℹ️  Charging continues as planned ({charging_current}A, {time_period} period)")
                        
            elif current_status == 'charger_end':
                print("🔍 Charging session ended - checking if should restart")
                if should_charge:
                    print(f"🚀 Starting new charging session ({time_period} period, {target_current}A)")
                    set_shelly_charging_state(config, True, target_current)
                    print("✅ Charging started")
                else:
                    print("ℹ️  Charging session ended and no charging allowed - staying idle")
                    
            else:
                print(f"ℹ️  Charger status: {current_status}")
                if should_charge and current_status in ['charger_free', 'charger_insert', 'charger_wait']:
                    print(f"🔌 Car available and charging allowed - starting charging ({target_current}A)")
                    set_shelly_charging_state(config, True, target_current)
                    print("✅ Charging started")
                else:
                    status_info = f"enabled={is_enabled}" if is_enabled else "disabled"
                    print(f"ℹ️  No action needed: Status={current_status}, {status_info}")
            
            return 0
                
        finally:
            cursor.close()
            connection.close()
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())