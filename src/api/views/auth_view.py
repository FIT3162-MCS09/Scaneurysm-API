from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.tokens import RefreshToken

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
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Include tokens in response
            response_data = serializer.data
            response_data['refresh'] = str(refresh)
            response_data['access'] = str(refresh.access_token)
            
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
            doctor = serializer.save()
            
            # The doctor model uses the User model's primary key
            # Get the user associated with this doctor
            user = doctor.user
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Include tokens in response
            response_data = serializer.data.copy()
            response_data['refresh'] = str(refresh)
            response_data['access'] = str(refresh.access_token)
            response_data['id'] = user.id  # Get the ID from the user object
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignInView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=SignInSerializer,
        responses={
            200: {'type': 'object', 'properties': {
                'refresh': {'type': 'string'},
                'access': {'type': 'string'},
                'user_id': {'type': 'string'},
                'username': {'type': 'string'},
                'email': {'type': 'string'},
                'role': {'type': 'string'}
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
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # If tracking sessions is still needed with JWT
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            expire_date = timezone.now() + timedelta(days=7)
            
            # Store JWT jti (unique identifier) instead of token
            session = UserSession.objects.create(
                user=user,
                token=str(refresh['jti']),  # Using JWT ID as identifier
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=request.data.get('device_info', ''),
                expires_at=expire_date,
            )
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

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
        try:
            # Get the JWT ID from the request
            jti = request.auth.get('jti', '')
            
            # Deactivate sessions with this JWT ID
            if jti:
                UserSession.objects.filter(token=jti).update(is_active=False)
                
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'Logout failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)