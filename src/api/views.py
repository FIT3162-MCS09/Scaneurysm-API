from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from rest_framework.serializers import Serializer
from rest_framework import serializers
from ml import shap_service, model_service
from utils.exception_handlers import handle_exceptions
import logging

logger = logging.getLogger(__name__)

class FeatureSerializer(Serializer):
    feature1 = serializers.FloatField(
        help_text="Value for feature 1",
        required=True
    )
    feature2 = serializers.FloatField(
        help_text="Value for feature 2",
        required=True
    )
    feature3 = serializers.FloatField(
        help_text="Value for feature 3",
        required=True
    )
    feature4 = serializers.FloatField(
        help_text="Value for feature 4",
        required=True
    )

# Input serializer with explicit fields
class FeaturesInputSerializer(Serializer):
    features = FeatureSerializer(
        help_text="Feature values for prediction"
    )

class PredictionOutputSerializer(Serializer):
    prediction = serializers.FloatField(
        help_text="Model prediction result"
    )
    feature_importance = serializers.DictField(
        child=serializers.FloatField(),
        help_text="SHAP values for each feature"
    )

class PredictionView(APIView):
    @handle_exceptions
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @extend_schema(
        request=FeaturesInputSerializer,
        responses={
            200: PredictionOutputSerializer,
            400: {"type": "object", "properties": {"error": {"type": "string"}}}
        },
        description="""
        Make a prediction and return SHAP explanations.
        
        This endpoint accepts feature values and returns both the prediction and feature importance values.
        All features (feature1, feature2, feature3, feature4) must be provided as float values.
        """,
        examples=[
            OpenApiExample(
                'Valid Input Example',
                value={
                    "features": {
                        "feature1": 0.5,
                        "feature2": 0.3,
                        "feature3": 0.7,
                        "feature4": 0.2
                    }
                },
                request_only=True,
                summary="Example feature values for prediction"
            ),
            OpenApiExample(
                'Success Response Example',
                value={
                    "prediction": 1.0,
                    "feature_importance": {
                        "feature1": 0.2,
                        "feature2": 0.3,
                        "feature3": -0.1,
                        "feature4": 0.4
                    }
                },
                response_only=True,
                summary="Example prediction result with feature importance"
            ),
        ],
        tags=['Prediction']
    )
    def post(self, request):
        """Make a prediction and return feature importance values"""
        try:
            serializer = FeaturesInputSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input format', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            features = serializer.validated_data['features']
            
            # Get both prediction and feature importance
            model= model_service.ModelService()
            prediction = model.predict(features)
            shap = shap_service.ShapService(model)
            feature_importance = shap.get_feature_importance(features)
            
            return Response({
                'prediction': prediction,
                'feature_importance': feature_importance
            })
        except Exception as e:
            logger.error("An error occurred: %s", str(e), exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )