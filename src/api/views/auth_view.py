from ..serializers.sign_up_serializer import PatientSerializer, DoctorSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from ..serializers.sign_in_serializer import SignInSerializer
class PatientSignUpView(APIView):
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorSignUpView(APIView):
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignInView(APIView):
    @extend_schema(
        request=SignInSerializer,
        responses={
            200: SignInSerializer,
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # login(request, user)
            return Response({"message": "Sign-in successful"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)