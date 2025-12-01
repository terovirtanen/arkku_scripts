#!/usr/bin/env python3
"""
Finds the cheapest consecutive 3-hour night period and all cheap day periods 
for electricity prices and saves them to database.
"""

import json
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
        
        # Day period configuration (hardcoded)
        'cheap_price_limit': 1.0,    # Price limit for cheap periods (c/kWh)
        'night_start_hour': 22,      # Night starts at 22:00
        'night_end_hour': 8,         # Night ends at 08:00
        'day_start_hour': 19         # Day period starts at 19:00
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


def create_charger_table(cursor):
    """Create car_charger table if it doesn't exist."""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS car_charger (
            id INT AUTO_INCREMENT PRIMARY KEY,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            average_price DECIMAL(10, 4) NOT NULL,
            period_type ENUM('night', 'day') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_start_time (start_time),
            INDEX idx_period_type (period_type)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'car_charger' created or already exists")
    except Error as e:
        print(f"Error creating car_charger table: {e}")
        raise


def save_period_to_db(cursor, start_time, end_time, avg_price, period_type):
    """Save charging period to database."""
    try:
        # Delete existing periods for today of this type
        date_str = start_time.strftime('%Y-%m-%d %H:%M')
        delete_query = """
        DELETE FROM car_charger 
        WHERE DATE(start_time) = %s AND period_type = %s
        """
        cursor.execute(delete_query, (date_str, period_type))
        
        # Insert new period
        insert_query = """
        INSERT INTO car_charger (start_time, end_time, average_price, period_type)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (start_time, end_time, avg_price, period_type))
        print(f"✓ Saved {period_type} period to database: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} (avg: {avg_price:.2f} c/kWh)")
        return True
    except Error as e:
        print(f"Error saving period to database: {e}")
        return False


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


def find_cheapest_3h_night_period(price_data, timezone):
    """Find the cheapest consecutive 3-hour period between today 22:00 and tomorrow 04:00."""
    # Find today's 22:00 and tomorrow's 04:00
    now = datetime.now(timezone)
    today_22 = now.replace(hour=22, minute=0, second=0, microsecond=0)
    
    # If it's already past 22:00 today, look at tonight's period
    if now.hour >= 22:
        night_start = today_22
    else:
        # If it's before 22:00, look at tonight's period starting at 22:00
        night_start = today_22
    
    # Tomorrow's 04:00 and 07:00 (naive datetime for comparison with database timestamps)
    tomorrow_4_naive = (night_start + timedelta(days=1)).replace(hour=4, minute=0, second=0, microsecond=0, tzinfo=None)
    tomorrow_7_naive = (night_start + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0, tzinfo=None)
    night_start_naive = night_start.replace(tzinfo=None)
    
    print(f"Searching for cheapest 3h period between {night_start.strftime('%Y-%m-%d %H:%M')} and {tomorrow_4_naive.strftime('%Y-%m-%d %H:%M')}")
    
    # Filter price data to only include the night period
    night_prices = []
    for timestamp, price in price_data:
        # Make sure timestamp is naive for comparison
        if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo is not None:
            timestamp_naive = timestamp.replace(tzinfo=None)
        else:
            timestamp_naive = timestamp
            
        if night_start_naive <= timestamp_naive <= tomorrow_7_naive:
            night_prices.append((timestamp_naive, price))
    
    if len(night_prices) < 12:  # Need at least 3 hours of data (12 x 15min intervals)
        print(f"Not enough night price data: {len(night_prices)} data points (need at least 12)")
        return None, float('inf'), []
    
    print(f"Found {len(night_prices)} price data points in night period")
    
    best_start = None
    best_avg_price = float('inf')
    best_period_prices = []
    
    # Check every possible 3-hour window within the night period
    sorted_night_prices = sorted(night_prices, key=lambda x: x[0])
    
    # Try starting a 3-hour window from each 15-minute interval
    for i in range(len(sorted_night_prices)):
        start_time = sorted_night_prices[i][0]
        end_time = start_time + timedelta(hours=3)
        
        # Make sure the 3-hour window starts before tomorrow 04:00
        if start_time > tomorrow_4_naive:
            break
        
        # Collect all prices within this 3-hour window
        window_prices = []
        for timestamp, price in sorted_night_prices:
            if start_time <= timestamp < end_time:
                window_prices.append((timestamp, float(price)))
        
        # Need sufficient data points for a reliable average
        if len(window_prices) < 12:  # At least 3 hours of data
            continue
        
        # Calculate average price for this window
        avg_price = sum(price for _, price in window_prices) / len(window_prices)
        
        print(f"Period {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}: {len(window_prices)} points, avg {avg_price:.2f} c/kWh")
        
        if avg_price < best_avg_price:
            best_avg_price = avg_price
            best_start = start_time
            best_period_prices = window_prices
            print(f"  ⭐ New best night period!")
    
    # Convert best_start back to timezone-aware for return
    if best_start is not None:
        best_start = timezone.localize(best_start)
    
    return best_start, best_avg_price, best_period_prices


def find_day_cheap_periods(price_data, night_avg_price, config, timezone):
    """Find all periods where price qualifies as cheap based on time periods:
    - 19:00-night_start: compare only to night average price
    - night_end-14:30: compare only to cheap_price_limit
    - 14:30-19:00: compare to both cheap_price_limit AND night average (either qualifies)
    Groups consecutive cheap periods."""
    # Sort all price data by timestamp
    sorted_prices = sorted(price_data, key=lambda x: x[0])
    
    cheap_price_limit = config['cheap_price_limit']
    night_start_hour = config['night_start_hour'] #22
    night_end_hour = config['night_end_hour'] # 8
    day_start_hour = config['day_start_hour'] #19
    
    print(f"\nFinding day periods with configuration:")
    print(f"  Cheap price limit: {cheap_price_limit:.2f} c/kWh")
    print(f"  Night hours: {night_start_hour}:00 - {night_end_hour:02d}:00")
    print(f"  Day starts at: {day_start_hour}:00")
    print(f"  Night average price: {night_avg_price:.2f} c/kWh")
    
    cheap_periods = []
    current_period_start = None
    current_period_prices = []
    
    now = datetime.now()

    # Find the night start time based on config
    night_start_time = now.replace(hour=night_start_hour, minute=0, second=0, microsecond=0, tzinfo=None)
    night_end_time = (now + timedelta(days=1)).replace(hour=night_end_hour, minute=0, second=0, microsecond=0, tzinfo=None)
    day_evening_start_time = now.replace(hour=day_start_hour, minute=0, second=0, microsecond=0, tzinfo=None)
    print(f"Night period starts at: {night_start_time.strftime('%Y-%m-%d %H:%M')}")
    
    for timestamp, price in sorted_prices:
        hour = timestamp.hour
        minute = timestamp.minute
        time_decimal = hour + minute / 60.0
        price_float = float(price)
        
        # Determine which time period we're in and what comparison to use
        price_qualifies = False
        comparison_text = None
        
        # day_start_hour - night_start (e.g., 19:00 - 22:00): compare only to night average
        if day_evening_start_time <= timestamp < night_start_time:
            if price_float <= night_avg_price:
                price_qualifies = True
                comparison_text = f"night avg ({night_avg_price:.2f})"
        
        # night_end (e.g., 08:00) - ...: compare only to cheap_price_limit
        elif night_end_time <= timestamp:
            if price_float <= cheap_price_limit:
                price_qualifies = True
                comparison_text = f"cheap limit ({cheap_price_limit:.2f})"
        
        # timestamp - day_evening_start_time: compare to both (either qualifies)
        elif timestamp < day_evening_start_time:
            if price_float <= cheap_price_limit:
                price_qualifies = True
                comparison_text = f"cheap limit ({cheap_price_limit:.2f})"
            elif price_float <= night_avg_price:
                price_qualifies = True
                comparison_text = f"night avg ({night_avg_price:.2f})"
        
        # Outside day periods - skip
        else:
            # End current period if we were in one
            if current_period_start:
                avg_price = sum(p for _, p in current_period_prices) / len(current_period_prices)
                end_time = current_period_prices[-1][0] + timedelta(minutes=15)
                cheap_periods.append((current_period_start, end_time, avg_price, current_period_prices))
                current_period_start = None
                current_period_prices = []
            continue
        
        if price_qualifies:
            if current_period_start is None:
                # Start new period
                current_period_start = timestamp
                current_period_prices = [(timestamp, price_float)]
                print(f"  Starting new day period at {timestamp.strftime('%H:%M')} ({price_float:.2f} c/kWh <= {comparison_text})")
            else:
                # Continue current period
                current_period_prices.append((timestamp, price_float))
        else:
            # Price too high, end current period if we were in one
            if current_period_start:
                avg_price = sum(p for _, p in current_period_prices) / len(current_period_prices)
                end_time = current_period_prices[-1][0] + timedelta(minutes=15)
                cheap_periods.append((current_period_start, end_time, avg_price, current_period_prices))
                print(f"  Ended day period: {current_period_start.strftime('%H:%M')}-{end_time.strftime('%H:%M')} (avg: {avg_price:.2f} c/kWh)")
                current_period_start = None
                current_period_prices = []
    
    # Handle period that extends to end of day
    if current_period_start:
        avg_price = sum(p for _, p in current_period_prices) / len(current_period_prices)
        end_time = current_period_prices[-1][0] + timedelta(minutes=15)
        cheap_periods.append((current_period_start, end_time, avg_price, current_period_prices))
        print(f"  Final day period: {current_period_start.strftime('%H:%M')}-{end_time.strftime('%H:%M')} (avg: {avg_price:.2f} c/kWh)")
    
    return cheap_periods


def main():
    """Main function that finds cheapest periods and saves them to database."""
    try:
        # Load configuration
        config = load_config()
        
        # Setup timezone
        timezone = pytz.timezone("Europe/Helsinki")
        
        # Calculate time range (from current hour to end of next day)
        now = datetime.now(timezone)
        start_time = now.replace(minute=0, second=0, microsecond=0)
        
        # End time is start of day after tomorrow (i.e., end of next day)
        next_day = start_time.date() + timedelta(days=1)
        end_time = timezone.localize(datetime.combine(next_day + timedelta(days=1), time(0, 0)))
        
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
            
            # Create car_charger table
            create_charger_table(cursor)
            
            # Find cheapest 3-hour night period
            best_start, best_avg_price, best_period_data = find_cheapest_3h_night_period(price_data, timezone)
            
            if best_start is None:
                print("No suitable 3-hour night period found between 22:00-04:00")
                return 1
            
            print(f"\n🌙 BEST NIGHT 3-HOUR PERIOD FOUND:")
            print(f"   Start time: {best_start.strftime('%Y-%m-%d %H:%M')}")
            print(f"   End time:   {(best_start + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M')}")
            print(f"   Average price: {best_avg_price:.2f} c/kWh")
            print(f"   Data points in period: {len(best_period_data)}")
            print(f"   Price range: {min(price for _, price in best_period_data):.2f} - {max(price for _, price in best_period_data):.2f} c/kWh")
            
            # Save night period to database
            night_end_time = best_start + timedelta(hours=3)
            save_period_to_db(cursor, best_start, night_end_time, best_avg_price, 'night')
            
            # Find cheap day periods
            day_periods = find_day_cheap_periods(price_data, best_avg_price, config, timezone)
            
            print(f"\n☀️ CHEAP DAY PERIODS FOUND ({len(day_periods)}):")
            for i, (start_time, end_time, avg_price, period_data) in enumerate(day_periods, 1):
                duration_hours = (end_time - start_time).total_seconds() / 3600
                print(f"   Period {i}: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} ({duration_hours:.1f}h)")
                print(f"     Average price: {avg_price:.2f} c/kWh")
                print(f"     Data points: {len(period_data)}")
                
                # Save day period to database
                save_period_to_db(cursor, start_time, end_time, avg_price, 'day')
            
            # Commit all changes
            connection.commit();
            
            print(f"\n✅ Charging schedule optimized successfully!")
            print(f"   Night period: {best_start.strftime('%H:%M')}-{night_end_time.strftime('%H:%M')}")
            print(f"   {len(day_periods)} additional day periods found")
            print(f"   All periods saved to database")
            return 0
                
        finally:
            cursor.close()
            connection.close()
            
    except Exception as e:
        print(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())