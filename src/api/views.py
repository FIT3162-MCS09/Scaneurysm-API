from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.serializers import Serializer
from rest_framework import serializers

# Input/Output serializers for documentation
class FeaturesInputSerializer(Serializer):
    features = serializers.DictField(
        child=serializers.FloatField(),
        help_text="Dictionary of feature values"
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Dummy data setup (no need to import real services)
        self.dummy_prediction = 1.0  # Dummy prediction result
        self.dummy_feature_importance = {
            'feature1': 0.2,
            'feature2': 0.3,
            'feature3': -0.1,
            'feature4': 0.4
        }

    @extend_schema(
        request=FeaturesInputSerializer,
        responses={200: PredictionOutputSerializer},
        description="Make a prediction and return SHAP explanations (dummy data for testing)",
        examples=[
            OpenApiExample(
                'Valid Input Example',
                value={
                    'features': {
                        'feature1': 0.5,
                        'feature2': 0.3,
                        'feature3': 0.7,
                        'feature4': 0.2
                    }
                },
                request_only=True,
            ),
            OpenApiExample(
                'Success Response Example',
                value={
                    'prediction': 1.0,
                    'feature_importance': {
                        'feature1': 0.2,
                        'feature2': 0.3,
                        'feature3': -0.1,
                        'feature4': 0.4
                    }
                },
                response_only=True,
            ),
        ]
    )
    def post(self, request):
        """Return dummy prediction and feature importance (SHAP values)"""
        try:
            features = request.data.get('features', {})
            
            # Return the dummy prediction and dummy feature importance
            return Response({
                'prediction': self.dummy_prediction,
                'feature_importance': self.dummy_feature_importance
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
