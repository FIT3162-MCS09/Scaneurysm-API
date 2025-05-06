from datetime import datetime
import uuid
import boto3
import json
from models.image_prediction import ImagePrediction
from django.conf import settings
from functools import lru_cache



class PredictionService:

    def __init__(self):
        self.shap_service = None

   
    def get_runtime_client(self):
        """
        Get or create boto3 runtime client with caching
        """
        return boto3.client('sagemaker-runtime')
    
    def get_endpoint_name(self):
        """
        Get the first available SageMaker endpoint name
        """
        try:
            # Create SageMaker client
            sagemaker_client = boto3.client('sagemaker')
            
            # List endpoints
            response = sagemaker_client.list_endpoints()
            
            # Get first endpoint name
            if response['Endpoints']:
                return response['Endpoints'][0]['EndpointName']
            raise Exception("No SageMaker endpoints found")
        except Exception as e:
            raise Exception(f"Error getting endpoint name: {str(e)}")

    def invoke_endpoint(self, image_url):
        """
        Invoke SageMaker endpoint with image URL
        """
        try:
            # Get runtime client
            runtime = self.get_runtime_client()
            
            # Get endpoint name
            endpoint_name = self.get_endpoint_name()
            
            # Prepare the input
            input_data = {
                "url": image_url
            }
            
            # Invoke endpoint
            response = runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='application/json',
                Body=json.dumps(input_data)
            )
            
            # Parse response
            result = json.loads(response['Body'].read().decode())
            return result
        except Exception as e:
            raise Exception(f"Error invoking SageMaker endpoint: {str(e)}")
            
    def perform_shap_analysis(self, image_url, user_id):
        """
        Invoke SHAP analysis Lambda function asynchronously and save request ID
        Returns request ID for tracking
        """
        try:
            lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
            request_id = str(uuid.uuid4())
            # Prepare Lambda event
            lambda_event = {
                "body": {
                    "image_url": image_url,
                    "user_id": str(user_id),
                    "request_id": request_id 
                }
            }
            
            # Invoke Lambda asynchronously
            response = lambda_client.invoke(
                FunctionName='shap-analysis',
                InvocationType='Event',  # This makes it async
                Payload=json.dumps(lambda_event)
            )
            
            
            return {
                'status': 'processing',
                'request_id': request_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error initiating SHAP analysis: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def check_shap_analysis_status(self, request_id, user_id):
        """
        Check the status of a SHAP analysis request and update ImagePrediction if completed
        """
        try:
            s3_client = boto3.client('s3')
            bucket = 'mcs09-bucket'
            try:
                prediction = ImagePrediction.objects.get(
                    request_id=request_id
                )
                
                try:
                    result = s3_client.get_object(
                        Bucket=bucket,
                        Key=f'requests/{str(prediction.user.id)}/{request_id}/result.json'  
                    )
                    result_data = json.loads(result['Body'].read().decode('utf-8'))
                    
                    # Update both the prediction JSON and the dedicated shap_explanation column
                    prediction_data = prediction.prediction or {}
                    prediction_data['shap_analysis'] = {
                        'status': 'completed',
                        'completion_time': datetime.utcnow().isoformat(),
                        'result': result_data
                    }
                    
                    prediction.prediction = prediction_data
                    prediction.shap_explanation = result_data  # Store in dedicated column
                    prediction.save()
                    
                    return {
                        'status': 'completed',
                        'result': result_data
                    }
                    
                except s3_client.exceptions.NoSuchKey:
                    # Check for error.json using the correct path structure
                    try:
                        error = s3_client.get_object(
                            Bucket=bucket,
                            Key=f'requests/{user_id}/{request_id}/error.json'  # Direct UUID path
                        )
                        error_data = json.loads(error['Body'].read().decode('utf-8'))
                        
                        # Update prediction with error status
                        prediction_data = prediction.prediction or {}
                        prediction_data['shap_analysis'] = {
                            'status': 'failed',
                            'error': error_data,
                            'completion_time': datetime.utcnow().isoformat()
                        }
                        
                        prediction.prediction = prediction_data
                        prediction.save()
                        
                        return {
                            'status': 'failed',
                            'error': error_data
                        }
                        
                    except s3_client.exceptions.NoSuchKey:
                        # If neither exists, it's still processing
                        return {
                            'status': 'processing',
                            'request_id': request_id
                        }
                        
            except ImagePrediction.DoesNotExist:
                return {
                    'status': 'error',
                    'error': f"No prediction found for request_id {request_id}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def create_prediction(self, user, image_url, include_shap=False):
        """
        Create and save prediction record with optional async SHAP analysis
        """
        try:
            prediction_result = self.invoke_endpoint(image_url)
            
            prediction_data = {
                'prediction': prediction_result
            }
            
            # Create prediction record with initial empty shap_explanation
            prediction = ImagePrediction.objects.create(
                user=user,
                image_url=image_url,
                prediction=prediction_data,
                shap_explanation=None  # Initialize empty shap_explanation
            )
            
            # If SHAP analysis is requested, initiate it
            if include_shap:
                shap_request = self.perform_shap_analysis(image_url, user.id)
                prediction.shap_explanation = shap_request
                prediction.prediction = prediction_data
                prediction.save()
            
            return prediction
                
        except Exception as e:
            raise Exception(f"Error creating prediction: {str(e)}")


    def get_user_predictions(self, user):
        """
        Get prediction history for a user and update any processing SHAP analyses
        """
        try:
            predictions = ImagePrediction.objects.filter(
                user=user
            ).order_by('-created_at')
            
            # Check and update status for predictions with processing SHAP analyses
            for prediction in predictions:
                prediction_data = prediction.prediction or {}
                shap_analysis = prediction_data.get('shap_analysis', {})
                
                # Check if SHAP analysis is in processing state
                if (shap_analysis.get('status') == 'processing' and 
                    'request_id' in shap_analysis):
                    # Update status
                    status = self.check_shap_analysis_status(
                        shap_analysis['request_id'], 
                        user.id
                    )
                    # Status update is handled within check_shap_analysis_status
                    # No need to manually update here as it's already saved to database
                    
            # Refresh queryset to get updated data
            predictions = ImagePrediction.objects.filter(
                user=user
            ).order_by('-created_at')
            
            return predictions
            
        except Exception as e:
            raise Exception(f"Error fetching predictions: {str(e)}")