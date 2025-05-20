import json
import sys
from datetime import datetime
import unittest
from unittest.mock import patch, MagicMock
import pytest

# Import and set up mocked dependencies
from .conftest import mock_torch

# Create a mock nn module
mock_nn = MagicMock()
mock_nn.Module = MagicMock
mock_nn.Conv2d = MagicMock
mock_nn.ReLU = MagicMock
mock_nn.MaxPool2d = MagicMock
mock_nn.Linear = MagicMock
mock_nn.Sequential = MagicMock

# Set up mock modules
mock_torch.nn = mock_nn
sys.modules['torch'] = mock_torch
sys.modules['torch.nn'] = mock_nn

# Now import after setting up mocks
from lambda_function import lambda_handler

class TestLambdaFunction(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures before each test"""
        self.test_event = {
            'body': json.dumps({
                'image_url': 'https://example.com/test.jpg',
                'user_id': 'test_user',
                'request_id': 'test_request_123'
            })
        }
        self.test_context = MagicMock()
        yield
    @patch('lambda_function.ShapAnalysisService')
    @patch('lambda_function.boto3.client')
    def test_successful_lambda_handler(self, mock_boto3_client, mock_shap_service):
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        # Mock ShapAnalysisService
        mock_service_instance = MagicMock()
        mock_service_instance.analyze_image.return_value = {
            'analysis_result': 'success'
        }
        mock_shap_service.return_value = mock_service_instance

        # Call lambda handler
        response = lambda_handler(self.test_event, self.test_context)

        # Assertions
        self.assertEqual(response['statusCode'], 202)
        self.assertEqual(
            json.loads(response['body'])['status'], 
            'processing'
        )
        
        # Verify S3 interactions
        mock_s3.put_object.assert_called()
        mock_service_instance.analyze_image.assert_called_once_with(
            'https://example.com/test.jpg',
            'test_user',
            'test_request_123'
        )

    def test_invalid_request_missing_parameters(self):
        # Test with missing parameters
        invalid_event = {
            'body': json.dumps({
                'image_url': 'https://example.com/test.jpg'
                # Missing user_id and request_id
            })
        }

        response = lambda_handler(invalid_event, self.test_context)
        
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('error', json.loads(response['body']))

    @patch('lambda_function.ShapAnalysisService')
    @patch('lambda_function.boto3.client')
    def test_error_handling(self, mock_boto3_client, mock_shap_service):
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        # Mock ShapAnalysisService to raise an exception
        mock_service_instance = MagicMock()
        mock_service_instance.analyze_image.side_effect = Exception('Test error')
        mock_shap_service.return_value = mock_service_instance

        # Call lambda handler
        response = lambda_handler(self.test_event, self.test_context)

        # Verify error was logged to S3
        mock_s3.put_object.assert_called_with(
            Bucket='mcs09-bucket',
            Key='requests/test_user/test_request_123/error.json',
            Body=unittest.mock.ANY,
            ContentType='application/json'
        )

if __name__ == '__main__':
    unittest.main()
