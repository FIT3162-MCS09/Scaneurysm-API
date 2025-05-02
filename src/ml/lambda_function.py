import json
from .shap_service import ShapAnalysisService

def lambda_handler(event, context):
    """
    AWS Lambda handler function for SHAP analysis
    """
    try:
        # Parse the request body
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        
        # Extract parameters
        image_url = body.get('image_url')
        user_id = body.get('user_id')
        
        if not image_url or not user_id:
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
        
        # Initialize service and analyze
        service = ShapAnalysisService()
        result = service.analyze_image(image_url, user_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'status': 'failed'
            })
        }