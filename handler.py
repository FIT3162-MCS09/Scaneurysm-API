import os
import sys

# Add the project root to the Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.core.settings')

# Import after setting up the environment
from src.core.wsgi import application

# Handler for AWS Lambda
def handler(event, context):
    return application(event, context)