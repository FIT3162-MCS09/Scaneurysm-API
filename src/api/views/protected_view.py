from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from drf_spectacular.utils import extend_schema

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={
            200: {'type': 'object', 'properties': {
                'id': {'type': 'string'},
                'username': {'type': 'string'},
                'email': {'type': 'string'},
                'role': {'type': 'string'},
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
            }},
            401: 'Unauthorized'
        }
    )
    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
        })