import os
import sys

# Get the absolute path to the src directory
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the src directory to Python path if it's not already there
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# RUN THE TEST WITH THIS IN THE DOCKER EXEC
# python -m pytest src/tests/ -v
