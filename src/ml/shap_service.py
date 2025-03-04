import shap
import numpy as np
from typing import Dict, Any, List, Union
from .model_service import ModelService

class ShapService:
    def __init__(self, model_service: ModelService):
        self.model_service = model_service
        self.explainer = None
        self.initialize_explainer()

    def initialize_explainer(self):
        """Initialize SHAP explainer with dummy background data"""
        # Create dummy background data matching the model's feature count
        n_features = len(self.model_service.get_feature_names())
        background_data = np.random.rand(100, n_features)
        self.explainer = shap.TreeExplainer(self.model_service.model, background_data)

    def get_feature_importance(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate SHAP values for given features"""
        if self.explainer is None:
            self.initialize_explainer()
        
        # Convert dictionary to numpy array
        feature_names = self.model_service.get_feature_names()
        X = np.array([features[name] for name in feature_names]).reshape(1, -1)
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(X)
        
        # Handle different types of SHAP value outputs
        if isinstance(shap_values, list):
            # For multi-class problems, take the positive class
            shap_values = shap_values[1]
        elif isinstance(shap_values, np.ndarray):
            # For binary classification or regression
            if shap_values.ndim > 2:
                shap_values = shap_values[..., 1]  # Take positive class for multi-class
        
        # Ensure we have a 2D array
        if shap_values.ndim == 1:
            shap_values = shap_values.reshape(1, -1)
            
        # Create feature importance dictionary using actual feature names
        return {name: float(value) for name, value in zip(feature_names, shap_values[0])}