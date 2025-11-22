#!/usr/bin/env python3
"""
Fetches electricity prices from Porssisähkö API and saves them to MySQL database.
"""

import json
import requests
from datetime import datetime
import pytz
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv


def create_database_and_table(connection, cursor):
    """Create database and table if they don't exist."""
    try:
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS porssisahkonet")
        print("Database 'porssisahkonet' created or already exists")
        
        # Use the database
        cursor.execute("USE porssisahkonet")
        
        # Create table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL UNIQUE,
            price DECIMAL(10, 4) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_timestamp (timestamp)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'prices' created or already exists")
        
    except Error as e:
        print(f"Error creating database/table: {e}")
        raise


def insert_price_data(cursor, timestamp, price):
    """Insert price data into database, ignore duplicates."""
    try:
        insert_query = """
        INSERT IGNORE INTO prices (timestamp, price) 
        VALUES (%s, %s)
        """
        cursor.execute(insert_query, (timestamp, price))
        return cursor.rowcount > 0
    except Error as e:
        print(f"Error inserting data: {e}")
        return False


def load_config():
    """Load and validate configuration from environment variables."""
    load_dotenv()
    
    config = {
        'db_host': os.getenv('DB_HOST', 'localhost'),
        'db_port': int(os.getenv('DB_PORT', 3306)),
        'db_username': os.getenv('DB_USERNAME'),
        'db_password': os.getenv('DB_PASSWORD')
    }
    
    if not config['db_username'] or not config['db_password']:
        raise ValueError("DB_USERNAME and DB_PASSWORD must be set in .env file")
    
    return config


def fetch_price_data():
    """Fetch electricity price data from Porssisähkö API."""
    try:
        response = requests.get('https://api.porssisahko.net/v2/latest-prices.json')
        response.raise_for_status()
        json_data = response.json()
        
        prices = json_data.get('prices', [])
        print(f"Fetched {len(prices)} price entries from API")
        return prices
        
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        raise


def create_database_connection(config, use_database=False):
    """Create MySQL database connection."""
    connection_params = {
        'host': config['db_host'],
        'port': config['db_port'],
        'user': config['db_username'],
        'password': config['db_password'],
        'charset': 'utf8mb4'
    }
    
    if use_database:
        connection_params['database'] = 'porssisahkonet'
    
    try:
        connection = mysql.connector.connect(**connection_params)
        print(f"Connected to MySQL server at {config['db_host']}:{config['db_port']}")
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        raise


def setup_database(config):
    """Setup database and tables, return connection ready for use."""
    # First connect without database to create it
    connection = create_database_connection(config, use_database=False)
    cursor = connection.cursor()
    
    try:
        create_database_and_table(connection, cursor)
    finally:
        cursor.close()
        connection.close()
    
    # Reconnect with database specified
    return create_database_connection(config, use_database=True)


def process_and_store_prices(cursor, price_entries, timezone):
    """Process price entries and store them in database."""
    inserted_count = 0
    
    for entry in price_entries:
        try:
            # Parse the start date
            start_date = datetime.fromisoformat(entry['startDate'].replace('Z', '+00:00'))
            start_date = start_date.astimezone(timezone)
            
            # Convert to MySQL datetime format
            timestamp = start_date.strftime('%Y-%m-%d %H:%M:%S')
            price = float(entry['price'])
            
            if insert_price_data(cursor, timestamp, price):
                inserted_count += 1
                
        except (ValueError, KeyError) as e:
            print(f"Error processing price entry: {e}")
            continue
    
    return inserted_count


def main():
    """Main function that orchestrates the electricity price data processing."""
    try:
        # Load configuration
        config = load_config()
        
        # Fetch price data from API
        price_entries = fetch_price_data()
        
        # Setup timezone
        timezone = pytz.timezone("Europe/Helsinki")
        
        # Setup database and get connection
        connection = setup_database(config)
        cursor = connection.cursor()
        
        try:
            # Process and store price data
            inserted_count = process_and_store_prices(cursor, price_entries, timezone)
            
            # Commit the changes
            connection.commit()
            print(f"Successfully inserted {inserted_count} new price records")
            
        except Exception as e:
            print(f"Error processing data: {e}")
            connection.rollback()
            raise
            
        finally:
            cursor.close()
            connection.close()
            print("Database connection closed")
            
    except Exception as e:
        print(f"Application error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    main()