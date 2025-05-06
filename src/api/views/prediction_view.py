from requests import request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from rest_framework.decorators import action
from models.image_prediction import ImagePrediction
from ..service.prediction_service import PredictionService
from ..serializers.prediction_serializer import ImagePredictionSerializer


class ImagePredictionView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    # serializer_class = ImagePredictionSerializer

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
                user=serializer.validated_data['user'],
                image_url=serializer.validated_data['image_url'],
                include_shap=serializer.validated_data.get('include_shap', False)
            )

            # Create a new serializer instance with the prediction object
            response_serializer = ImagePredictionSerializer(prediction)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

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
    def update_shap_statuses(self, request):
        # """Update SHAP analysis statuses for a user's predictions"""
        try:
            # Get user from request data or use authenticated user
            user_id = request.data.get('user_id')
            user = request.user
            if user_id:
                user = user_id

            # Get predictions and update SHAP statuses
            predictions = self.prediction_service.get_user_predictions(user)
            
            # Serialize and return updated predictions
            serializer = ImagePredictionSerializer(predictions, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @extend_schema(
        parameters=[
            OpenApiParameter(name='user_id', description='ID of the user', required=True, type=str),
            OpenApiParameter(name='request_id', description='ID of the request', required=True, type=str)
        ],
        responses={
            200: 'Good Request',
            400: 'Bad Request'
        }
    )
    def check_shap_status(self, request):
        """
        Check the status of a prediction analysis
        """
        try:
            request_id = request.query_params.get('request_id')
            user_id = request.query_params.get('user_id')
            if not request_id and user_id:
                return Response(
                    {'error': 'request_id and user_id are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            status_result = self.prediction_service.check_shap_analysis_status(
                request_id=request_id,
                user_id=user_id
            )

            if status_result.get('status') == 'error':
                return Response(
                    status_result,
                    status=status.HTTP_404_NOT_FOUND if 'not found' in status_result.get('error', '') 
                    else status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(status_result)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )