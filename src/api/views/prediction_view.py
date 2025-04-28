from requests import request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from rest_framework.decorators import action
from models.image_prediction import ImagePrediction
from ..service.prediction_service import PredictionService
from ..serializers.prediction_serializer import ImagePredictionSerializer


class ImagePredictionView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ImagePredictionSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prediction_service = PredictionService()

    @extend_schema(
        request=ImagePredictionSerializer,
        responses={
            200: ImagePredictionSerializer,
            400: {"type": "object", "properties": {"error": {"type": "string"}}}
        }
    )
    def create_prediction(self, request):
        try:
            # Add user to request data if not provided
            data = request.data.copy()
            if 'user' not in data:
                data['user'] = request.user.id
                
            serializer = ImagePredictionSerializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            prediction = self.prediction_service.create_prediction(
                user=serializer.validated_data['user'],  # Use user from serializer
                image_url=serializer.validated_data['image_url']
            )

            return Response(ImagePredictionSerializer(prediction).data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='user_id',
                description='ID of the user to get predictions for',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='prediction_id',
                description='ID of the specific prediction to retrieve',
                required=False,
                type=int
            )
        ],
        responses={
            200: ImagePredictionSerializer(many=True),
            404: {"type": "object", "properties": {"error": {"type": "string"}}}
        }
    )
    def get_history(self, request):
        """Get prediction history by user ID and/or specific prediction"""
        try:
            user_id = request.query_params.get('user_id')
            prediction_id = request.query_params.get('prediction_id')

            # Base query
            queryset = ImagePrediction.objects

            # Filter by user_id if provided, otherwise use authenticated user
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            else:
                queryset = queryset.filter(user=request.user)

            # Filter by prediction_id if provided
            if prediction_id:
                prediction = queryset.filter(id=prediction_id).first()
                if not prediction:
                    return Response({
                        'error': 'Prediction not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                serializer = ImagePredictionSerializer(prediction)
                return Response(serializer.data)

            # Get all predictions for the user
            predictions = queryset.order_by('-created_at')
            serializer = ImagePredictionSerializer(predictions, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)