import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError

def create_notebook_instance(
    notebook_name="mcs09-notebook",
    instance_type="ml.t2.medium",
    region_name="ap-southeast-1"
):
    """Create a SageMaker notebook instance"""
    sagemaker = boto3.client('sagemaker', region_name=region_name)
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    try:
        # First check if the role exists, if not create it
        iam = boto3.client('iam')
        role_name = "SageMakerExecutionRole-krooldonutz"
        role_arn = None
        
        try:
            role = iam.get_role(RoleName=role_name)
            role_arn = role['Role']['Arn']
            print(f"✓ Found existing IAM role: {role_name}")
        except iam.exceptions.NoSuchEntityException:
            print(f"Creating new IAM role: {role_name}")
            
            # Create the IAM role
            trust_relationship = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "sagemaker.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            role = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_relationship)
            )
            role_arn = role['Role']['Arn']
            
            # Attach required policies
            policies = [
                'arn:aws:iam::aws:policy/AmazonSageMakerFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess'
            ]
            
            for policy in policies:
                iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
            
            # Wait for role to be available
            print("Waiting for role to be ready...")
            time.sleep(10)
        
        # Create the notebook instance
        print(f"\nCreating notebook instance: {notebook_name}")
        sagemaker.create_notebook_instance(
            NotebookInstanceName=notebook_name,
            InstanceType=instance_type,
            RoleArn=role_arn,
            Tags=[
                {
                    'Key': 'Creator',
                    'Value': 'krooldonutz'
                }
            ]
        )
        
        # Wait for the notebook to be in service
        print("Waiting for notebook instance to be ready...")
        waiter = sagemaker.get_waiter('notebook_instance_in_service')
        waiter.wait(
            NotebookInstanceName=notebook_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 60
            }
        )
        
        print(f"✓ Notebook instance '{notebook_name}' created successfully!")
        
        # Get the notebook URL
        url_response = sagemaker.create_presigned_notebook_instance_url(
            NotebookInstanceName=notebook_name
        )
        print(f"\nNotebook URL: {url_response['AuthorizedUrl']}")
        
        return True
        
    except Exception as e:
        print(f"Error creating notebook instance: {str(e)}")
        return False

def get_or_create_sagemaker_endpoint(
    model_name="resnet50-shap",  # Changed to match our model name
    instance_type="ml.t2.medium",
    region_name="ap-southeast-1"  # Changed to match our previous setup
):
    print(f"Starting endpoint check/creation process at {datetime.utcnow()}")
    
    # Initialize SageMaker client
    sagemaker = boto3.client('sagemaker', region_name=region_name)
    
    # Get account ID
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    # Define bucket name using our previously created bucket
    bucket_name = f"sagemaker-krooldonutz-{account_id}"
    
    try:
        endpoints = sagemaker.list_endpoints()
        print("\nExisting endpoints:")
        for endpoint in endpoints['Endpoints']:
            print(f"- {endpoint['EndpointName']} (Status: {endpoint['EndpointStatus']}")
    except Exception as e:
        print(f"Error listing endpoints: {str(e)}")
        return None

    # Generate unique endpoint name
    timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    endpoint_name = f"{model_name}-endpoint-{timestamp}"
    
    try:
        # Create model using our ResNet50 configuration
        print(f"\nCreating model: {model_name}")
        sagemaker.create_model(
            ModelName=model_name,
            PrimaryContainer={
                # Using PyTorch inference container for ResNet50
                'Image': '763104351884.dkr.ecr.ap-southeast-1.amazonaws.com/pytorch-inference:1.8.1-cpu-py36-ubuntu18.04',
                'ModelDataUrl': f's3://{bucket_name}/model.tar.gz',
                'Environment': {
                    'SAGEMAKER_SUBMIT_DIRECTORY': '/opt/ml/model',
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_MODEL_SERVER_TIMEOUT': '3600'
                }
            },
            ExecutionRoleArn=f"arn:aws:iam::{account_id}:role/SageMakerExecutionRole-krooldonutz"
        )
        
        # Create endpoint configuration
        print(f"Creating endpoint configuration: {endpoint_name}-config")
        sagemaker.create_endpoint_config(
            EndpointConfigName=f"{endpoint_name}-config",
            ProductionVariants=[{
                'VariantName': 'default',  # Changed to match our previous config
                'ModelName': model_name,
                'InstanceType': instance_type,
                'InitialInstanceCount': 1,
                'InitialVariantWeight': 1
            }]
        )
        
        # Create endpoint
        print(f"Creating endpoint: {endpoint_name}")
        sagemaker.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=f"{endpoint_name}-config"
        )
        
        # Wait for endpoint to be ready
        print("Waiting for endpoint to be ready...")
        waiter = sagemaker.get_waiter('endpoint_in_service')
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 60
            }
        )
        
        print(f"\nEndpoint {endpoint_name} created successfully!")
        
        # Save endpoint information to a more comprehensive config file
        config = {
            'endpoint_name': endpoint_name,
            'model_name': model_name,
            'bucket_name': bucket_name,
            'region': region_name,
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'instance_type': instance_type
        }
        
        # Save to both .env and a JSON config file
        with open('.env', 'a') as f:
            f.write(f"\nSAGEMAKER_ENDPOINT_NAME={endpoint_name}")
            f.write(f"\nSAGEMAKER_REGION={region_name}")
            f.write(f"\nSAGEMAKER_BUCKET={bucket_name}")
        
        with open('sagemaker_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return endpoint_name
        
    except Exception as e:
        print(f"Error creating endpoint: {str(e)}")
        return None

def check_endpoint_status(endpoint_name, region_name="ap-southeast-1"):
    """Check the status of a specific endpoint"""
    sagemaker = boto3.client('sagemaker', region_name=region_name)
    
    try:
        response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
        return {
            'EndpointName': endpoint_name,
            'Status': response['EndpointStatus'],
            'LastModified': response['LastModifiedTime'].strftime('%Y-%m-%d %H:%M:%S'),
            'CreationTime': response['CreationTime'].strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'EndpointName': endpoint_name,
            'Status': 'Error',
            'Error': str(e)
        }

def verify_resources():
    """Verify that all required resources exist"""
    region = "ap-southeast-1"
    account_id = boto3.client('sts').get_caller_identity()['Account']
    bucket_name = f"sagemaker-krooldonutz-{account_id}"
    
    print("Verifying AWS resources...")
    
    # Check S3 bucket
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"✓ S3 bucket '{bucket_name}' exists")
    except Exception:
        print(f"✗ S3 bucket '{bucket_name}' not found")
        return False
    
    # Check IAM role
    iam = boto3.client('iam')
    role_name = "SageMakerExecutionRole-krooldonutz"
    try:
        iam.get_role(RoleName=role_name)
        print(f"✓ IAM role '{role_name}' exists")
    except Exception:
        print(f"✗ IAM role '{role_name}' not found")
        print(f"Error details: {str(e)}")
        return False
    
    # Check/Create notebook instance
    sagemaker = boto3.client('sagemaker', region_name=region)
    notebook_name = "mcs09-notebook"
    try:
        response = sagemaker.describe_notebook_instance(NotebookInstanceName=notebook_name)
        print(f"✓ Notebook instance '{notebook_name}' exists ({response['NotebookInstanceStatus']})")
    except ClientError:
        print(f"Creating notebook instance '{notebook_name}'...")
        if not create_notebook_instance():
            print("✗ Failed to create notebook instance")
            return False
        
    return True

if __name__ == "__main__":
    region = "ap-southeast-1"  # Changed to match our previous setup
    
    print("=== SageMaker Endpoint Management ===")
    print(f"User: krooldonutz")
    print(f"Current UTC time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Region: {region}")
    
    # Verify resources first
    if not verify_resources():
        print("\nSome required resources are missing. Please run the setup commands first.")
        exit(1)
    
    # List existing endpoints
    sagemaker = boto3.client('sagemaker', region_name=region)
    endpoints = sagemaker.list_endpoints()
    
    if endpoints['Endpoints']:
        print("\nExisting endpoints:")
        for endpoint in endpoints['Endpoints']:
            status = check_endpoint_status(endpoint['EndpointName'])
            print(json.dumps(status, indent=2))
    else:
        print("\nNo existing endpoints found.")
        create = input("Would you like to create a new endpoint? (y/n): ")
        if create.lower() == 'y':
            endpoint_name = get_or_create_sagemaker_endpoint()
            if endpoint_name:
                print(f"\nEndpoint configuration saved!")
                print(f"Use these settings in your Django environment:")
                print(f"SAGEMAKER_ENDPOINT_NAME={endpoint_name}")
                print(f"SAGEMAKER_REGION={region}")
                print(f"Check sagemaker_config.json for complete configuration.")