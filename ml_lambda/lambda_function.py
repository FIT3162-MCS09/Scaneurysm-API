import json
import boto3
import uuid
from datetime import datetime
from shap_service import ShapAnalysisService

def lambda_handler(event, context):
    """
    AWS Lambda handler function for async SHAP analysis
    """
    try:
        # Parse the request body
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        
        # Extract parameters
        image_url = body.get('image_url')
        user_id = body.get('user_id')
        request_id = body.get('request_id')
        
        if not image_url or not user_id or not request_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameters: image_url and user_id'
                })
            }

        timestamp = datetime.utcnow().isoformat()
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        results_bucket = 'mcs09-bucket'  # Use your existing bucket
        
        # Store the initial request
        request_data = {
            'request_id': request_id,
            'user_id': user_id,
            'image_url': image_url,
            'status': 'processing',
            'timestamp': timestamp
        }
        
        # Save request metadata to S3
        s3_client.put_object(
            Bucket=results_bucket,
            Key=f'requests/{user_id}/{request_id}/request.json',
            Body=json.dumps(request_data),
            ContentType='application/json'
        )
        
        # Initialize service and analyze
        service = ShapAnalysisService()
        result = service.analyze_image(image_url, user_id, request_id)
        
        # Update the request status and store results
        result.update({
            'request_id': request_id,
            'status': 'completed',
            'completion_time': datetime.utcnow().isoformat()
        })
        
        # Save complete results to S3
        s3_client.put_object(
            Bucket=results_bucket,
            Key=f'requests/{user_id}/{request_id}/result.json',
            Body=json.dumps(result),
            ContentType='application/json'
        )
        
        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'request_id': request_id,
                'status': 'processing',
                'message': 'Analysis started successfully'
            })
        }
        
    except Exception as e:
        error_response = {
            'error': str(e),
            'status': 'failed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if 'request_id' in locals():
            error_response['request_id'] = request_id
            # Save error to S3
            s3_client.put_object(
                Bucket=results_bucket,
                Key=f'requests/{user_id}/{request_id}/error.json',
                Body=json.dumps(error_response),
                ContentType='application/json'
            )
            
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(error_response)
        }