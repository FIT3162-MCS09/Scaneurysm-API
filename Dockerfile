# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for the required libraries (like compilers)
RUN apt-get update && apt-get install -y \
    build-essential \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt first to take advantage of Docker cache
COPY requirements.txt /app/

# Install pip and upgrade it
RUN python -m pip install --upgrade pip

# Install the required Python packages from requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the project files into the container
COPY . /app/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application (adjusted to point to the manage.py file in src/)
# CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]