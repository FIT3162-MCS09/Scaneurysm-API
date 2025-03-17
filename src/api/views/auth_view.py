from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema

# Fix import paths according to your project structure
from models.user import User  # Adjust if needed
from models.user_session import UserSession  # Adjust if needed
from ..serializers.sign_in_serializer import SignInSerializer
from ..serializers.sign_up_serializer import PatientSerializer, DoctorSerializer

class PatientSignUpView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=PatientSerializer,
        responses={
            201: PatientSerializer,
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create token for new user
            token, _ = Token.objects.get_or_create(user=user)
            
            # Include token in response
            response_data = serializer.data
            response_data['token'] = token.key
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorSignUpView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=DoctorSerializer,
        responses={
            201: DoctorSerializer,
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = DoctorSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create token for new user
            token, _ = Token.objects.get_or_create(user=user)
            
            # Include token in response
            response_data = serializer.data
            response_data['token'] = token.key
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignInView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=SignInSerializer,
        responses={
            200: {'type': 'object', 'properties': {
                'token': {'type': 'string'},
                'user_id': {'type': 'string'},
                'username': {'type': 'string'},
                'email': {'type': 'string'},
                'role': {'type': 'string'},
                'expires_at': {'type': 'string', 'format': 'date-time'}
            }},
            400: 'Bad Request',
            401: 'Unauthorized'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Record login info
            ip_address = self.get_client_ip(request)
            user.record_login(ip_address)
            
            # Get or create token
            token, _ = Token.objects.get_or_create(user=user)
            
            # Create session record
            expire_date = timezone.now() + timedelta(days=7)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            session = UserSession.objects.create(
                user=user,
                token=token.key,
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=request.data.get('device_info', ''),
                expires_at=expire_date,
            )
            
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'expires_at': expire_date.isoformat(),
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

# Adding LogoutView and SessionListView
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={
            200: {'type': 'object', 'properties': {
                'message': {'type': 'string'}
            }}
        }
    )
    def post(self, request):
        # Deactivate all sessions with this token
        UserSession.objects.filter(token=request.auth.key).update(is_active=False)
        
        # Delete the token
        request.auth.delete()
        
        return Response({
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)


class SessionListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={
            200: {'type': 'array', 'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'device_info': {'type': 'string'},
                    'ip_address': {'type': 'string'},
                    'user_agent': {'type': 'string'},
                    'created_at': {'type': 'string', 'format': 'date-time'},
                    'expires_at': {'type': 'string', 'format': 'date-time'},
                    'is_current': {'type': 'boolean'}
                }
            }}
        }
    )
    def get(self, request):
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')
        
        sessions_data = [{
            'id': str(session.id),
            'device_info': session.device_info,
            'ip_address': session.ip_address,
            'user_agent': session.user_agent,
            'created_at': session.created_at.isoformat(),
            'expires_at': session.expires_at.isoformat(),
            'is_current': session.token == request.auth.key
        } for session in sessions]
        
        return Response(sessions_data, status=status.HTTP_200_OK)
    
    @extend_schema(
        request={'type': 'object', 'properties': {
            'session_id': {'type': 'string'}
        }},
        responses={
            200: {'type': 'object', 'properties': {
                'message': {'type': 'string'}
            }},
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    def delete(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({
                'error': 'Session ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=request.user,
                is_active=True
            )
            
            # Don't allow deleting current session through this endpoint
            if session.token == request.auth.key:
                return Response({
                    'error': 'Cannot delete current session. Use logout instead.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Deactivate session
            session.is_active = False
            session.save()
            
            # Delete the token if it exists
            Token.objects.filter(key=session.token).delete()
            
            return Response({
                'message': 'Session successfully terminated'
            }, status=status.HTTP_200_OK)
            
        except UserSession.DoesNotExist:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)