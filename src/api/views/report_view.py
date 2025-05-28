from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from ..service.report_service import ReportService
from ..service.gen_ai_service import GenAiService
from ..service.prediction_service import PredictionService


class ReportView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.report_service = ReportService(
            gen_ai_service=GenAiService(),
            prediction_service=PredictionService()
        )

    @extend_schema(
        responses={
            200: {"type": "object"},
            404: {"type": "object", "properties": {"error": {"type": "string"}}},
            500: {"type": "object", "properties": {"error": {"type": "string"}}}
        }
    )
    def get(self, request):
        """
        Get the latest AI analysis for the authenticated user
        """
        try:
            user_id = request.user.id

            analysis = self.report_service.get_latest_ai_analysis_by_user_id(user_id)
            if not analysis:
                return Response(
                    {'error': 'No analysis found for the user'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(analysis)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("An error occurred while processing the request", exc_info=True)
            return Response(
                {'error': 'An internal error has occurred. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
