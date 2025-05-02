# FIT3162_MCS09 Backend Service

A Django-based backend service that provides SHAP (SHapley Additive exPlanations) analysis for image classification using a CNN model.

## Features

- REST API endpoints for image analysis
- SHAP analysis integration with PyTorch models
- JWT authentication
- AWS Lambda integration for ML processing
- S3 integration for model storage and results
- MySQL database support
- CORS support
- Rate limiting for API endpoints

## Prerequisites

- Python 3.10+
- Docker (for containerization)
- AWS account with proper credentials
- MySQL database

## Environment Variables

The following environment variables need to be configured:

```env
DB_NAME=mcs09
USER=<database_user>
PASS=<database_password>
ENDPOINT=<database_endpoint>
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd FIT3162_MCS09_backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start the development server:
```bash
python manage.py runserver
```

## API Documentation

The API is documented using drf-spectacular. Access the Swagger UI at:
```
/api/docs
```

### Main Endpoints

- POST `/api/shap-analysis/`: Perform SHAP analysis on an image
  - Requires authentication
  - Accepts image URL in request body
  - Returns SHAP analysis results

## Deployment

The application is containerized and deployed using AWS ECS. Deployment is automated via GitHub Actions workflow.

### AWS Lambda Deployment

The ML processing is handled by AWS Lambda. To deploy the Lambda function:

1. Navigate to the `ml_lambda` directory
2. Build the Docker image:
```bash
docker build -t shap-analysis-lambda .
```

3. Push to AWS ECR and deploy using the provided AWS CloudFormation templates

## Configuration

Key configuration files:
- `src/core/settings.py`: Django settings
- `.aws/task-definition.json`: ECS task definition
- `ml_lambda/Dockerfile`: Lambda container configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

