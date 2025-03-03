import shap
import numpy as np
from typing import Dict, Any
from .model_service import ModelService

class ShapService:
    def __init__(self, model_service: ModelService):
        self.model_service = model_service
        self.explainer = None
        self.initialize_explainer()

    def initialize_explainer(self):
        """Initialize SHAP explainer with dummy background data"""
        # Create dummy background data
        background_data = np.random.rand(100, len(self.model_service.model.feature_importances_))
        self.explainer = shap.TreeExplainer(self.model_service.model, background_data)

    def get_feature_importance(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate SHAP values for given features"""
        if self.explainer is None:
            self.initialize_explainer()
        
        # Convert dictionary to numpy array
        X = np.array(list(features.values())).reshape(1, -1)
        shap_values = self.explainer.shap_values(X)
        
        # For binary classification, shap_values might be a list with two elements
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Take positive class values
            
        return {f'feature_{i}': float(value) for i, value in enumerate(shap_values[0])}