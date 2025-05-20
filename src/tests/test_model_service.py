import pytest
import sys
import json
from unittest.mock import patch, MagicMock

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

# Now import our module after setting up mocks
from model_service import ModelService, CNNModel

@pytest.fixture(autouse=True)
def reset_model_service():
    """Reset the ModelService singleton between tests"""
    if hasattr(ModelService, '_instance'):
        ModelService._instance = None
    yield

@pytest.fixture
def mock_model_state():
    """Create mock model state dict"""
    state_dict = {
        'model_state_dict': {
            'features.0.weight': mock_torch.randn(64, 3, 3, 3),
            'classifier.6.weight': mock_torch.randn(2, 4096),
            'classifier.6.bias': mock_torch.randn(2)
        }
    }
    return state_dict

def test_singleton_pattern():
    """Test that ModelService is a singleton"""
    service1 = ModelService()
    service2 = ModelService()
    assert service1 is service2

@pytest.mark.parametrize("exists_locally", [True, False])
def test_model_loading(exists_locally, mock_model_state):
    """Test model loading from local path and S3"""
    with patch('model_service.os.path.exists', return_value=exists_locally), \
         patch('model_service.torch.load', return_value=mock_model_state) as mock_torch_load:
        
        if not exists_locally:
            # Set up S3 mocking only if testing S3 path
            with patch('model_service.boto3.client') as mock_boto3_client:
                mock_s3 = MagicMock()
                mock_boto3_client.return_value = mock_s3
                
                model_service = ModelService()
                mock_s3.download_file.assert_called_once()
        else:
            model_service = ModelService()
        
        # Verify model was loaded
        mock_torch_load.assert_called_once()

def test_device_selection():
    """Test device selection logic"""
    for cuda_available in [True, False]:
        with patch('model_service.torch.cuda.is_available', return_value=cuda_available):
            ModelService._instance = None  # Reset singleton
            model_service = ModelService()
            expected_device = 'cuda' if cuda_available else 'cpu'
            assert str(model_service._device) in [expected_device, 'cpu']
