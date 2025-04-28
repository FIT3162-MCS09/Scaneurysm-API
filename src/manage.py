#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import pymysql
import time
import boto3
from botocore.config import Config
from typing import Optional

class ConnectionManager:
    _db_instance: Optional[pymysql.Connection] = None
    _s3_instance: Optional[boto3.resource] = None
    _sagemaker_instance: Optional[boto3.client] = None

    @classmethod
    def get_db_connection(cls) -> pymysql.Connection:
        """Establish database connection with retry logic"""
        if cls._db_instance is not None:
            try:
                cls._db_instance.ping(reconnect=True)
                return cls._db_instance
            except:
                cls._db_instance = None

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
                cls._db_instance = connection
                return connection
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Connection attempt {attempt + 1} failed: {str(e)}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"All connection attempts failed: {str(e)}")
                    raise

    @classmethod
    def get_s3_connection(cls) -> boto3.resource:
        """Establish S3 connection"""
        if cls._s3_instance is not None:
            return cls._s3_instance

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
            
            cls._s3_instance = s3
            return s3
        except Exception as e:
            print(f"Failed to connect to S3: {str(e)}")
            raise

    @classmethod
    def get_sagemaker_runtime(cls) -> boto3.client:
        """Establish SageMaker runtime connection"""
        if cls._sagemaker_instance is not None:
            return cls._sagemaker_instance

        try:
            # Configure boto3 client with retry settings
            config = Config(
                retries=dict(max_attempts=3),
                connect_timeout=5,
                read_timeout=60
            )

            sagemaker_runtime = boto3.client(
                'sagemaker-runtime',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_REGION', 'ap-southeast-1'),
                config=config
            )

            print("SageMaker runtime connection initialized")
            
            # Test the connection by checking endpoint
            endpoint_name = os.environ.get('SAGEMAKER_ENDPOINT_NAME')
            if endpoint_name:
                print(f"Verifying SageMaker endpoint: {endpoint_name}")
                # List endpoints to verify connection
                sagemaker = boto3.client('sagemaker')
                endpoints = sagemaker.list_endpoints()
                if any(endpoint['EndpointName'] == endpoint_name for endpoint in endpoints['Endpoints']):
                    print(f"SageMaker endpoint {endpoint_name} verified")
                else:
                    print(f"Warning: Endpoint {endpoint_name} not found")

            cls._sagemaker_instance = sagemaker_runtime
            return sagemaker_runtime

        except Exception as e:
            print(f"Failed to initialize SageMaker runtime: {str(e)}")
            raise

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    # Initialize all connections
    try:
        # Database connection
        conn = ConnectionManager.get_db_connection()
        print("Database connection established successfully")
        
        # S3 connection
        ConnectionManager.get_s3_connection()
        print("S3 connection established successfully")
        
        # SageMaker connection
        ConnectionManager.get_sagemaker_runtime()
        print("SageMaker runtime connection established successfully")

    except Exception as e:
        print(f"Failed to initialize connections: {str(e)}")
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