from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

class HealthView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        description='Health check endpoint',
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "ok"}
                }
            }
        }
    )
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)