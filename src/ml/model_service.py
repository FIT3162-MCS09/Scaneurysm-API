from django.conf import settings
import torch
import torch.nn as nn
from torchvision import models
from datetime import datetime
import os
import boto3

class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()
        # Initialize VGG16 with pretrained weights
        self.vgg16 = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1)

        # Freeze feature layers
        for param in self.vgg16.features.parameters():
            param.requires_grad = False

        # Modify the classifier
        in_features = self.vgg16.classifier[6].in_features
        self.vgg16.classifier[6] = nn.Linear(in_features, 2)

    def forward(self, x):
        return self.vgg16(x)

class ModelService:
    _instance = None
    _model = None
    _device = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            print(f"\nInitializing ModelService at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"User: krooldonutz")
            cls._instance = super(ModelService, cls).__new__(cls)
            # Initialize here instead of in __init__
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if not self._initialized:
            self._initialized = True
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"Using device: {self._device}")
            self._load_model()

    def __init__(self):
        # Remove initialization from here
        pass

    def _load_model(self):
        try:
            model_path = None
            
            # Try local paths first
            possible_paths = [
                'src/api/model.pth',
                'api/model.pth',
                'model.pth',
                os.path.join(os.path.dirname(__file__), '..', 'api', 'model.pth'),
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break

            # If model not found locally, try downloading from S3
            if model_path is None:
                print("Model not found locally, attempting to download from S3...")
                model_path = self._download_model_from_s3()

            # If still no model found, raise error
            if model_path is None:
                raise FileNotFoundError("Could not find or download model.pth")

            print(f"Loading model from: {model_path}")
            
            # Initialize model
            self._model = CNNModel().to(self._device)
            
            # Load state dict
            state_dict = torch.load(model_path, map_location=self._device)
            
            # Handle different types of saved states
            if isinstance(state_dict, dict):
                if 'model_state_dict' in state_dict:
                    state_dict = state_dict['model_state_dict']
                elif 'state_dict' in state_dict:
                    state_dict = state_dict['state_dict']

            # Load the state dict
            incompatible_keys = self._model.load_state_dict(state_dict, strict=False)
            
            # Print loading results
            if incompatible_keys.missing_keys:
                print("\nMissing keys:")
                for key in incompatible_keys.missing_keys:
                    print(f"- {key}")
            if incompatible_keys.unexpected_keys:
                print("\nUnexpected keys:")
                for key in incompatible_keys.unexpected_keys:
                    print(f"- {key}")

            self._model.eval()
            print("✓ Model loaded successfully and set to evaluation mode")

        except Exception as e:
            print(f"\n❌ Error loading model: {str(e)}")
            raise

    def get_model(self):
        return self._model

    def get_device(self):
        return self._device
    
    def _download_model_from_s3(self):
        """Download model from S3 if in production environment"""
        try:
            s3 = boto3.client('s3')
            bucket_name = 'pytorch-model-mcs09'
            model_key = 'model.pth'
            local_path = 'src/api/model.pth'
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            print(f"Downloading model from S3: s3://{bucket_name}/{model_key}")
            
            # Download the file
            s3.download_file(
                bucket_name,
                model_key,
                local_path
            )
            print(f"✓ Model downloaded successfully to: {local_path}")
            return local_path
        except Exception as e:
            print(f"❌ Error downloading model from S3: {str(e)}")
            return None