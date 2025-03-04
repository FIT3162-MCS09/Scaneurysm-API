import joblib
import numpy as np
from typing import Dict, Any, List
from django.conf import settings
import os
from utils.exception_handlers import handle_exceptions
import logging

logger = logging.getLogger(__name__)

class ModelService:
    @handle_exceptions
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.load_model()

    def load_model(self):
        """Load the ML model from disk"""
        model_path = os.path.join(settings.MODEL_DIR, 'model.joblib')
        try:
            self.model = joblib.load(model_path)
            # Initialize feature names (modify this according to your actual feature names)
            self.feature_names = [f'feature_{i}' for i in range(self.model.n_features_in_)]
        except FileNotFoundError:
            # For demonstration, create a simple model
            from sklearn.ensemble import RandomForestClassifier
            n_features = 4
            self.model = RandomForestClassifier(n_estimators=10)
            self.model.fit(np.random.rand(100, n_features), np.random.randint(2, size=100))
            self.feature_names = [f'feature_{i}' for i in range(n_features)]
            # Save the model
            os.makedirs(settings.MODEL_DIR, exist_ok=True)
            joblib.dump(self.model, model_path)

    def predict(self, features: Dict[str, Any]) -> np.ndarray:
        """Make predictions using the loaded model"""
        if self.model is None:
            self.load_model()
        # Convert dictionary to numpy array using feature names order
        X = np.array([features[name] for name in self.feature_names]).reshape(1, -1)
        return self.model.predict(X)

    def get_feature_names(self) -> List[str]:
        """Get the list of feature names in the correct order"""
        return self.feature_names