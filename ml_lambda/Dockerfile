# Use slim base image
FROM public.ecr.aws/lambda/python:3.10

# Install only necessary system dependencies
RUN yum update -y && \
    yum install -y \
    gcc \
    gcc-c++ \
    python3-devel \
    && yum clean all && \
    rm -rf /var/cache/yum

# Create and set permissions for tmp directories
RUN mkdir -p /tmp/.cache/torch /tmp/.cache/matplotlib /tmp/model && \
    chmod -R 777 /tmp/.cache && \
    chmod -R 777 /tmp/model

# Copy only necessary files
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies with size optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    # Install PyTorch with minimal dependencies
    pip install --no-cache-dir \
    torch==2.0.0 --index-url https://download.pytorch.org/whl/cpu \
    torchvision==0.15.0 --index-url https://download.pytorch.org/whl/cpu \
    # Install other requirements
    && pip install --no-cache-dir -r requirements.txt \
    # Clean up pip cache
    && find /var/lang/lib/python3.10/site-packages -name "*.pyc" -delete \
    && find /var/lang/lib/python3.10/site-packages -name "tests" -type d -exec rm -rf {} + \
    && rm -rf /root/.cache/pip

# Copy your lambda function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY shap_service.py ${LAMBDA_TASK_ROOT}
COPY model_service.py ${LAMBDA_TASK_ROOT}

# Set environment variables
ENV MPLCONFIGDIR=/tmp
ENV PYTHONUNBUFFERED=1

# Set the CMD to your handler
CMD [ "lambda_function.lambda_handler" ]