import logging
import traceback
from django.http import JsonResponse
from datetime import datetime

logger = logging.getLogger(__name__)

class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Handle any unhandled exceptions"""
        # Get the full traceback
        error_traceback = traceback.format_exc()
        
        # Log the error with traceback
        logger.error(f"""
        Exception occurred at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
        User: {request.user}
        Path: {request.path}
        Method: {request.method}
        Error: {str(exception)}
        Traceback:
        {error_traceback}
        """)

        # Return JSON response for API endpoints
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': str(exception),
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'path': request.path,
                'type': exception.__class__.__name__
            }, status=500)
        
        # Let Django's default exception handler handle non-API requests
        return None