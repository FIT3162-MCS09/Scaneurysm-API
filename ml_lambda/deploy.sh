#!/bin/bash
set -e

# # Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🚀 Starting deployment process..."

# # Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# # Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install and configure AWS CLI first."
    exit 1
fi

# # Build the Docker image with required platform and provenance settings
echo "🔨 Building Docker image..."
docker buildx build --platform linux/amd64 --provenance=false -t ml-lambda:latest .

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="ap-southeast-1"  # from your zappa_settings.json
REPO_NAME="ml-lambda"
ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"

# # Login to ECR
echo "🔑 Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URI}

# # Create ECR repository if it doesn't exist
# if ! aws ecr describe-repositories --repository-names ${REPO_NAME} &> /dev/null; then
#     echo "📦 Creating ECR repository..."
#     aws ecr create-repository \
#         --repository-name ${REPO_NAME} \
#         --region ${AWS_REGION} \
#         --image-scanning-configuration scanOnPush=true \
#         --image-tag-mutability MUTABLE
# fi

# # Tag and push the image to ECR
# echo "📤 Pushing image to ECR..."
docker tag ml-lambda:latest ${ECR_REPO_URI}:latest
docker push ${ECR_REPO_URI}:latest

echo "🔄 Creating/Updating Lambda function..."
FUNCTION_NAME="shap-analysis"
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole"

# Check if Lambda function exists
if aws lambda get-function --function-name ${FUNCTION_NAME} &> /dev/null; then
    echo "🔄 Updating existing Lambda function..."
    # Update function code
    aws lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --image-uri ${ECR_REPO_URI}:latest

    # Update function configuration
    aws lambda update-function-configuration \
        --function-name ${FUNCTION_NAME} \
        --memory-size 2048 \
        --timeout 900 \
        --environment "Variables={PYTHONUNBUFFERED=1,MPLCONFIGDIR=/tmp}"
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name ${FUNCTION_NAME} \
        --package-type Image \
        --code ImageUri=${ECR_REPO_URI}:latest \
        --role ${ROLE_ARN} \
        --memory-size 2048 \
        --timeout 900 \
        --environment "Variables={PYTHONUNBUFFERED=1,MPLCONFIGDIR=/tmp}"
fi

# Add function URL (if needed)
if ! aws lambda get-function-url-config --function-name ${FUNCTION_NAME} &> /dev/null; then
    echo "🌐 Creating function URL..."
    aws lambda create-function-url-config \
        --function-name ${FUNCTION_NAME} \
        --auth-type NONE \
        --cors '{"AllowOrigins": ["*"], "AllowMethods": ["POST"], "AllowHeaders": ["*"], "ExposeHeaders": ["*"]}'
fi

echo "✅ Deployment completed successfully!"