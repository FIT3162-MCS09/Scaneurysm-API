from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..serializers.shap_analysis_serializer import ShapAnalysisRequestSerializer
from ml.shap_service import ShapAnalysisService
from drf_spectacular.utils import extend_schema, OpenApiResponse


class ShapAnalysisView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shap_service = ShapAnalysisService()


    @extend_schema(
        request=ShapAnalysisRequestSerializer,
        responses={
            200: OpenApiResponse(description="SHAP analysis completed successfully"),
            400: OpenApiResponse(description="Invalid input data"),
            500: OpenApiResponse(description="Internal server error")
        },
        description="Analyze an image using SHAP and return the results",
        tags=["SHAP Analysis"]
    )
    def post(self, request):
        serializer = ShapAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = self.shap_service.analyze_image(serializer.validated_data['image_url'])
            
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )