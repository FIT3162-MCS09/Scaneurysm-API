import boto3
import json
from models.image_prediction import ImagePrediction
from django.conf import settings
from functools import lru_cache

class PredictionService:
    @lru_cache(maxsize=1)
    def get_runtime_client(self):
        """
        Get or create boto3 runtime client with caching
        """
        return boto3.client('sagemaker-runtime')
    
    @lru_cache(maxsize=1)
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

    def create_prediction(self, user, image_url):
        """
        Create and save prediction record
        
        Args:
            user: User instance
            image_url: URL of the image to predict
            
        Returns:
            ImagePrediction: Created prediction record
            
        Raises:
            Exception: If prediction creation or endpoint invocation fails
        """
        try:
            # Get prediction from SageMaker endpoint
            prediction_result = self.invoke_endpoint(image_url)
            
            # Create and save prediction record
            prediction = ImagePrediction.objects.create(
                user=user,
                image_url=image_url,
                prediction=prediction_result
            )
            return prediction
        except Exception as e:
            raise Exception(f"Error creating prediction: {str(e)}")

    def get_user_predictions(self, user):
        """
        Get prediction history for a user
        """
        try:
            predictions = ImagePrediction.objects.filter(
                user=user
            ).order_by('-created_at')
            return predictions
        except Exception as e:
            raise Exception(f"Error fetching predictions: {str(e)}")