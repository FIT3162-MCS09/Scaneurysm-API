#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import pymysql
import time

def get_db_connection():
    """Establish database connection with retry logic"""
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Connecting to {os.environ.get('ENDPOINT', 'DB_ENDPOINT not set')}")
            connection = pymysql.connect(
                host=os.environ.get('ENDPOINT'),
                user=os.environ.get('USER'),
                password=os.environ.get('PASS'),
                connect_timeout=5
            )
            print(f"Connection successful to {os.environ.get('ENDPOINT')}")
            return connection
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Connection attempt {attempt + 1} failed: {str(e)}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"All connection attempts failed: {str(e)}")
                raise

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    # Try to establish database connection
    try:
        conn = get_db_connection()
        print("Database connection established successfully")
        conn.close()
    except Exception as e:
        print(f"Failed to connect to database: {str(e)}")
        # You might want to exit here if database connection is crucial
        # sys.exit(1)
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()