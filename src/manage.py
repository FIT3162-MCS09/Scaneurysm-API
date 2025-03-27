#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import pymysql
import time
import boto3


def get_db_connection():
    """Establish database connection with retry logic"""
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Connecting to {os.environ.get('ENDPOINT', 'DB_ENDPOINT not set')}")
            connection = pymysql.connect(
                host=os.environ.get('ENDPOINT'),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASS'),
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

def get_s3_connection():
    
    try:
        # Print connection information with fallback messages
        print(f"AWS Access Key ID: {'*****' if os.environ.get('AWS_ACCESS_KEY_ID') else 'AWS_ACCESS_KEY_ID not set'}")
        print(f"AWS Secret Access Key: {'*****' if os.environ.get('AWS_SECRET_ACCESS_KEY') else 'AWS_SECRET_ACCESS_KEY not set'}")
        print(f"AWS Region: {os.environ.get('AWS_REGION', 'ap-southeast-1')}")
        
        # Create S3 resource with environment variables
        s3 = boto3.resource(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'ap-southeast-1')
        )
        
        # List all buckets
        for bucket in s3.buckets.all():
            print(bucket.name)
        
        return s3
    except Exception as e:
        print(f"Failed to connect to S3: {str(e)}")
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
        sys.exit(1)
    
    try:
        get_s3_connection()
        print("S3 connection established successfully")
    except Exception as e:
        print(f"Failed to connect to S3: {str(e)}")
        # You might want to exit here if S3 connection is crucial
        sys.exit(1)
    
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