import unittest
from unittest.mock import patch, MagicMock

# Mock Django settings and models before importing PredictionService
import sys
from unittest.mock import MagicMock

# Mock Django settings
settings_mock = MagicMock()
sys.modules['django.conf'] = MagicMock()
sys.modules['django.conf'].settings = settings_mock

# Mock Django models
image_prediction_mock = MagicMock()
sys.modules['models.image_prediction'] = MagicMock()
sys.modules['models.image_prediction'].ImagePrediction = image_prediction_mock

# Now import PredictionService after mocking dependencies
from api.service.prediction_service import PredictionService


class TestPredictionService(unittest.TestCase):
    def setUp(self):
        self.service = PredictionService()
        # Mock user
        self.user = MagicMock()
        self.user.username = 'testuser'
        self.user.email = 'test@example.com'
        self.test_image_url = "https://example.com/test.jpg"

    @patch('boto3.client')
    def test_get_endpoint_name(self, mock_boto3_client):
        # Mock the SageMaker client response
        mock_sagemaker = MagicMock()
        mock_sagemaker.list_endpoints.return_value = {
            'Endpoints': [{'EndpointName': 'test-endpoint'}]
        }
        mock_boto3_client.return_value = mock_sagemaker

        endpoint_name = self.service.get_endpoint_name()
        self.assertEqual(endpoint_name, 'test-endpoint')


if __name__ == '__main__':
    unittest.main()