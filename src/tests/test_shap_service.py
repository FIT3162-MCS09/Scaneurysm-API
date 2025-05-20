import pytest
import sys
from unittest.mock import patch, MagicMock

# Import mocked dependencies from conftest
from .conftest import mock_torch

# Create a mock nn module
mock_nn = MagicMock()
mock_nn.Module = MagicMock
mock_nn.Conv2d = MagicMock
mock_nn.ReLU = MagicMock
mock_nn.MaxPool2d = MagicMock
mock_nn.Linear = MagicMock
mock_nn.Sequential = MagicMock
mock_torch.nn = mock_nn

# Set up mock modules
sys.modules['torch'] = mock_torch
sys.modules['torch.nn'] = mock_nn
mock_sns = MagicMock()
mock_sns.heatmap = MagicMock()
sys.modules['seaborn'] = mock_sns

# Set up mock for torch.nn.Module
mock_nn.Module = MagicMock

# Create a mock instance for CNNModel that behaves like a torch.nn.Module
cnn_instance = MagicMock()
cnn_instance.features = MagicMock()
cnn_instance.classifier = MagicMock()
cnn_instance.eval = MagicMock(return_value=cnn_instance)
cnn_instance.train = MagicMock(return_value=cnn_instance)
cnn_instance.to = MagicMock(return_value=cnn_instance)
cnn_instance.forward = MagicMock()
cnn_instance.load_state_dict = MagicMock()

# Create mock tensor with proper comparison behavior
mock_tensor = MagicMock()
mock_tensor.item = MagicMock(return_value=0.9)  # High confidence prediction
mock_tensor.__gt__ = lambda _, x: mock_tensor.item() > x
mock_probs = MagicMock()
mock_probs.__getitem__ = lambda _, idx: mock_tensor

# Set up model output behavior
output = MagicMock()
mock_nn.functional.softmax.return_value = mock_probs

# Create a mock class for CNNModel
mock_cnn_class = MagicMock()
mock_cnn_class.return_value = cnn_instance

# Set up the patches before importing any modules that use CNNModel
_patcher1 = patch('model_service.CNNModel', mock_cnn_class)
_patcher2 = patch('shap_service.CNNModel', mock_cnn_class)
_patcher1.start()
_patcher2.start()

# Import required libraries
import sys
from unittest.mock import MagicMock, patch
from shap_service import ShapAnalysisService

@pytest.fixture
def test_params():
    """Test parameters used across tests"""
    return {
        'user_id': 'test_user',
        'request_id': 'test_request_123'
    }

@pytest.fixture
def mock_model():
    """Create a mock model"""
    mock_model = MagicMock()
    mock_model.features = MagicMock()
    mock_model.eval = MagicMock(return_value=mock_model)
    mock_model.to = MagicMock(return_value=mock_model)
    return mock_model

@pytest.fixture
def shap_service(mock_model):
    """Create a SHAP service instance with mocked dependencies"""
    with patch('shap_service.CNNModel') as mock_cnn:
        mock_cnn.return_value = mock_model
        service = ShapAnalysisService()
        service.model = mock_model  # Ensure we're using our mock
        return service

@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    """Mock external dependencies"""
    # Mock numpy
    mock_numpy = MagicMock()
    mock_values = MagicMock()
    # Mock numpy array behaviors
    mock_values.shape = (1, 224, 224, 3)
    mock_values.__getitem__ = lambda _, idx: mock_values
    mock_numpy.zeros = MagicMock(return_value=mock_values)
    
    # Create another mock for mean result that has shape attribute
    mock_mean_result = MagicMock()
    mock_mean_result.shape = (224, 224)  # Expected shape after mean reduction
    mock_numpy.mean = MagicMock(return_value=mock_mean_result)
    
    mock_numpy.abs = MagicMock(return_value=mock_values)
    mock_numpy.std = MagicMock(return_value=0.1)
    mock_numpy.min = MagicMock(return_value=0)
    mock_numpy.max = MagicMock(return_value=1)
    mock_numpy.sum = MagicMock(return_value=1.0)
    
    # Add advanced numpy behaviors
    mock_numpy.expand_dims = MagicMock(return_value=mock_values)
    mock_mean_result.__truediv__ = lambda _, x: mock_mean_result  # For division operations
    mock_mean_result.__add__ = lambda _, x: mock_mean_result  # For addition operations
    # Mock numpy globally
    sys.modules['numpy'] = mock_numpy
    sys.modules['np'] = mock_numpy
    monkeypatch.setattr('shap_service.np', mock_numpy)
    
    # Mock SHAP
    mock_explanation = MagicMock()
    mock_explanation.values = mock_values
    
    mock_explainer = MagicMock()
    mock_explainer_instance = MagicMock()
    mock_explainer_instance.__call__ = MagicMock(return_value=mock_explanation)
    mock_explainer.return_value = mock_explainer_instance
    
    mock_masker = MagicMock()
    mock_masker.return_value = MagicMock()
    
    mock_shap = MagicMock()
    mock_shap.Explainer = mock_explainer
    mock_shap.maskers.Image = mock_masker
    mock_shap.Explanation = MagicMock()
    mock_shap.Explanation.argsort.flip = [0]  # Mock the expected output structure
    monkeypatch.setattr('shap_service.shap', mock_shap)

    # Create a proper mock for torch tensors with numeric comparisons
    def create_tensor_mock(value):
        tensor = MagicMock()
        tensor.item = MagicMock(return_value=value)
        tensor.__gt__ = lambda _, x: value > x
        tensor.__ge__ = lambda _, x: value >= x
        tensor.__lt__ = lambda _, x: value < x
        tensor.__le__ = lambda _, x: value <= x
        tensor.__float__ = lambda _: float(value)
        tensor.cpu = MagicMock(return_value=tensor)
        tensor.numpy = MagicMock(return_value=mock_values)
        return tensor

    # Create tensor mocks with proper confidence values
    mock_probs = MagicMock()
    mock_probs.cpu = MagicMock(return_value=mock_probs)
    mock_probs.numpy = MagicMock(return_value=mock_values)
    
    high_conf_tensor = create_tensor_mock(0.9)  # High confidence prediction
    low_conf_tensor = create_tensor_mock(0.1)   # Low confidence prediction
    
    mock_probs.__getitem__ = lambda _, idx: high_conf_tensor if isinstance(idx, tuple) or idx == 1 else [low_conf_tensor, high_conf_tensor]
    mock_output = high_conf_tensor

    # Set up model prediction
    mock_argmax = create_tensor_mock(1)  # Predict class 1 (aneurysm)
    mock_probs.argmax = MagicMock(return_value=mock_argmax)
    mock_argmax.dim = MagicMock(return_value=1)

    # Mock torch.nn.functional
    mock_functional = MagicMock()
    mock_functional.softmax = MagicMock(return_value=mock_probs)
    mock_nn.functional = mock_functional

    # Set up model output
    mock_model = MagicMock()
    mock_model.eval = MagicMock(return_value=mock_model)
    mock_model.to = MagicMock(return_value=mock_model)
    mock_model.forward = MagicMock(return_value=mock_output)
    mock_model.parameters = MagicMock(return_value=iter([MagicMock()]))
    
    # Mock image processing
    mock_pil_image = MagicMock()
    mock_image = MagicMock()
    mock_image.size = (224, 224)
    mock_pil_image.return_value = mock_image
    monkeypatch.setattr('PIL.Image.open', mock_pil_image)
    
    # Mock OpenCV
    mock_cv2 = MagicMock()
    mock_cv2.cvtColor.return_value = mock_values
    mock_cv2.resize.return_value = mock_values
    monkeypatch.setattr('shap_service.cv2', mock_cv2)
    
    # Mock requests
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake image data"
    mock_requests = MagicMock()
    mock_requests.get.return_value = mock_response
    monkeypatch.setattr('shap_service.requests', mock_requests)
    
    # Mock matplotlib
    mock_plt = MagicMock()
    mock_plt.figure = MagicMock()
    mock_plt.subplot = MagicMock()
    mock_plt.imshow = MagicMock()
    mock_plt.title = MagicMock()
    mock_plt.axis = MagicMock()
    mock_plt.savefig = MagicMock()
    mock_plt.close = MagicMock()
    monkeypatch.setattr('matplotlib.pyplot', mock_plt)
    
    # Mock seaborn
    monkeypatch.setattr('shap_service.sns', sys.modules['seaborn'])
    
    # Mock PIL
    mock_image = MagicMock()
    mock_image.size = (224, 224)  # Add expected image size
    mock_image_module = MagicMock()
    mock_image_module.open.return_value = mock_image
    mock_image_module.fromarray.return_value = mock_image
    monkeypatch.setattr('shap_service.Image', mock_image_module)
    
    # Mock cv2
    mock_cv2 = MagicMock()
    mock_cv2.cvtColor.return_value = mock_values  # Use the same mock values from above
    mock_cv2.resize.return_value = mock_values
    mock_cv2.COLOR_BGR2RGB = 4  # Dummy value for color conversion flag
    monkeypatch.setattr('shap_service.cv2', mock_cv2)
    
    return mock_shap

def test_shap_analysis_pipeline(shap_service, test_params, mock_model):
    """Test the complete SHAP analysis pipeline"""
    # Mock the S3 client
    mock_s3 = MagicMock()
    patch('shap_service.boto3.client', return_value=mock_s3).start()
    
    # Test the analysis
    result = shap_service.analyze_image(
        image_url="https://example.com/test.jpg",
        user_id=test_params['user_id'],
        request_id=test_params['request_id']
    )
    
    # Verify basic expectations
    assert result is not None
    assert not isinstance(result, Exception)
    assert 'error' not in result
    
    # Verify model was used properly
    assert mock_model.eval.called
    
    # Verify all expected result keys are present
    assert 'prediction' in result
    assert 'analysis' in result
    assert 'metadata' in result
    assert 'visualization' in result
    
    # Verify prediction structure
    pred = result['prediction']
    assert 'result' in pred
    assert 'confidence' in pred
    assert 'confidence_level' in pred
    
    # Verify analysis structure
    analysis = result['analysis']
    assert 'most_important_quadrant' in analysis
    assert 'quadrant_scores' in analysis
    assert 'relative_importances' in analysis
    assert 'stability_score' in analysis
    assert 'importance_score' in analysis

def test_error_handling(shap_service, test_params, monkeypatch):
    """Test error handling in SHAP analysis"""
    # Mock requests to fail
    mock_requests = MagicMock()
    mock_requests.get.side_effect = Exception("Test error")
    monkeypatch.setattr('shap_service.requests', mock_requests)
    
    # Test with invalid inputs
    result = shap_service.analyze_image(
        image_url="https://example.com/bad.jpg",
        user_id=test_params['user_id'],
        request_id=test_params['request_id']
    )
    
    # Verify error response
    assert result.get('status') == 'failed'
    assert 'error' in result
