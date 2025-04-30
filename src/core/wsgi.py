import os
import sys
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Add the project root directory to Python path
root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root)

# Configure Django settings with correct path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.core.settings')

try:
    import django
    django.setup()
    logger.debug("Django setup completed successfully")
except Exception as e:
    logger.error(f"Failed to setup Django: {str(e)}")
    raise e

try:
    from src.core.wsgi import application
    logger.debug("WSGI application imported successfully")
except Exception as e:
    logger.error(f"Failed to import WSGI application: {str(e)}")
    raise e

def handler(event, context):
    """
    Lambda handler function
    """
    try:
        logger.debug(f"Received event: {event}")
        logger.debug(f"Python path: {sys.path}")
        logger.debug(f"Current working directory: {os.getcwd()}")
        logger.debug(f"Directory contents: {os.listdir('.')}")
        
        return application(event, context)
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        raise e