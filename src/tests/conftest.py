import os
import sys
from unittest.mock import MagicMock, patch
import pytest
import django
from django.conf import settings

# Get absolute paths first
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ml_lambda_path = os.path.abspath(os.path.join(os.path.dirname(src_path), 'ml_lambda'))

# Add paths to Python path
sys.path.insert(0, src_path)
sys.path.insert(0, ml_lambda_path)

# Configure Django settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

# Set up mock objects first before any patches
mock_torch = MagicMock()
mock_torch.device = lambda x: x
mock_torch.cuda = MagicMock()
mock_torch.cuda.is_available = MagicMock(return_value=False)
mock_torch.load = MagicMock(return_value={'model_state_dict': {}})
mock_torch.nn = MagicMock()
mock_torch.nn.functional = MagicMock()
mock_torch.tensor = lambda x: x
mock_torch.stack = lambda x: x
mock_torch.nn.functional.softmax = lambda x, dim: x
mock_torch.no_grad = MagicMock()
mock_torch.no_grad.return_value.__enter__ = MagicMock()
mock_torch.no_grad.return_value.__exit__ = MagicMock()
mock_torch.randn = lambda *args: MagicMock()

mock_np = MagicMock()
mock_np.array = lambda x: x
mock_np.float32 = float
mock_np.uint8 = int
mock_np.mean = lambda x, axis=None: 0.5
mock_np.std = lambda x: 0.0
mock_np.abs = lambda x: x
mock_np.sum = lambda x: 1.0
mock_np.expand_dims = lambda x, axis: x
mock_np.min = lambda x: 0
mock_np.max = lambda x: 1

mock_transforms = MagicMock()
mock_transforms.Compose = lambda x: lambda y: y
mock_transforms.Resize = MagicMock(return_value=lambda x: x)
mock_transforms.ToTensor = MagicMock(return_value=lambda x: x)
mock_transforms.Normalize = lambda **kwargs: lambda x: x

mock_pil = MagicMock()
mock_pil.Image = MagicMock()
mock_pil.Image.open = MagicMock(return_value=MagicMock(size=(224, 224)))

mock_s3_client = MagicMock()
mock_boto3 = MagicMock()
mock_boto3.client.return_value = mock_s3_client
mock_s3_client.download_file = MagicMock()
mock_s3_client.put_object = MagicMock()

mock_shap = MagicMock()
mock_shap.Explainer = MagicMock(return_value=MagicMock())
mock_shap.maskers = MagicMock()
mock_shap.maskers.Image = MagicMock(return_value=MagicMock())

# Create mock model class
class MockCNNModel(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.features = MagicMock()
        self.classifier = MagicMock()
        self.to = MagicMock(return_value=self)
        self.eval = MagicMock(return_value=self)
        self.parameters = MagicMock(return_value=iter([MagicMock()]))
        self.load_state_dict = MagicMock()
        self.forward = MagicMock(return_value=mock_torch.tensor([0.7, 0.3]))
        self.state_dict = MagicMock(return_value={
            'features.0.weight': mock_torch.randn(64, 3, 3, 3),  
            'features.0.bias': mock_torch.randn(64),
            'classifier.6.weight': mock_torch.randn(2, 4096),
            'classifier.6.bias': mock_torch.randn(2)
        })

# Set up Django settings
mock_settings = MagicMock()
mock_settings.SECRET_KEY = 'dummy_key'
mock_settings.DEBUG = True

MOCK_MODULES = {
    'torch': mock_torch,
    'numpy': mock_np,
    'PIL': mock_pil,
    'PIL.Image': mock_pil.Image,
    'torchvision': MagicMock(),
    'torchvision.transforms': mock_transforms,
    'boto3': mock_boto3,
    'shap': mock_shap,
    'matplotlib': MagicMock(),
    'matplotlib.pyplot': MagicMock(),
    'seaborn': MagicMock(),
    'cv2': MagicMock(),
    'botocore': MagicMock(),
    'botocore.exceptions': MagicMock(),
    'django.conf': MagicMock(),
    'django.db': MagicMock(),
    'django.db.models': MagicMock(),
    'django': MagicMock(),
    'io': MagicMock()
}

# Apply mocks before any test imports
for mod_name, mock in MOCK_MODULES.items():
    sys.modules[mod_name] = mock

# Set Django settings after module mocks
sys.modules['django.conf'].settings = mock_settings

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the ModelService singleton before each test"""
    try:
        from model_service import ModelService
        ModelService._instance = None
        ModelService._model = None
        ModelService._device = None
        ModelService._initialized = False
    except ImportError:
        pass  # Module might not be imported yet
    yield

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Set up test environment and mocks"""
    patches = [
        patch.dict('sys.modules', MOCK_MODULES),
        patch('model_service.CNNModel', MockCNNModel),
        patch('model_service.os.path.exists', return_value=True),
        patch('model_service.torch.cuda.is_available', return_value=False)
    ]
    
    for p in patches:
        p.start()
        
    yield
    
    for p in reversed(patches):
        p.stop()
