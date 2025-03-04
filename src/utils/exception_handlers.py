import functools
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

def handle_exceptions(func):
    """Decorator to handle exceptions in any function"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get the full traceback
            error_traceback = traceback.format_exc()
            
            # Log the error with context
            logger.error(f"""
            Exception in {func.__name__} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            Args: {args}
            Kwargs: {kwargs}
            Error: {str(e)}
            Traceback:
            {error_traceback}
            """)
            
            # Re-raise the exception
            raise
    
    return wrapper