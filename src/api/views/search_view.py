from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from serializers.file_serializer import FileUploadSerializer, 
from serializers import FileSerializer
from serializers.sign_up_serializer import PatientSerializer, DoctorSerializer
from service.upload_service import UploadService
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.permissions import AllowAny

class PatientSearchView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='user_id', description='ID of the user', required=True, type=str)
        ],
        responses={
            200: PatientSerializer,
            404: OpenApiResponse(
                description="Patient not found",
                response={"type": "object", "properties": {"error": {"type": "string"}}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Fetch the patient object using the user_id
            patient = Patient.objects.get(user_id=user_id)
            
            # Serialize the patient object
            serializer = PatientSerializer(patient)
            
            # Return the serialized data
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

class DoctorSearchView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='user_id', description='ID of the user', required=True, type=str)
        ],
        responses={
            200: DoctorSerializer,
            404: OpenApiResponse(
                description="Doctor not found",
                response={"type": "object", "properties": {"error": {"type": "string"}}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Fetch the doctor object using the user_id
            doctor = Doctor.objects.get(user_id=user_id)
            
            # Serialize the doctor object
            serializer = DoctorSerializer(doctor)
            
            # Return the serialized data
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

class UserSearchView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='first_name', description='First name of the user to search for', required=False, type=str),
            OpenApiParameter(name='last_name', description='Last name of the user to search for', required=False, type=str),
            OpenApiParameter(name='email', description='Email of the user to search for', required=False, type=str),
        ],
        responses={
            200: OpenApiResponse(
                description="Successful search",
                response={
                    "type": "object",
                    "properties": {
                        "doctors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"},
                                    "email": {"type": "string"}
                                }
                            }
                        },
                        "patients": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"},
                                    "email": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            ),
            404: OpenApiResponse(
                description="No users found",
                response={"type": "object", "properties": {"error": {"type": "string"}}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        first_name = request.query_params.get('first_name')
        last_name = request.query_params.get('last_name')
        email = request.query_params.get('email')

        if not first_name and not last_name and not email:
            return Response({"error": "At least one search parameter (first_name, last_name, or email) is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Filter users based on the provided parameters
        filters = {}
        if first_name:
            filters['first_name__icontains'] = first_name  # Case-insensitive partial match
        if last_name:
            filters['last_name__icontains'] = last_name  # Case-insensitive partial match
        if email:
            filters['email__icontains'] = email  # Case-insensitive partial match

        users = User.objects.filter(**filters)

        if not users.exists():
            return Response({"error": "No users found"}, status=status.HTTP_404_NOT_FOUND)

        # Divide users into doctors and patients
        doctors = users.filter(role='doctor')  # Assuming 'role' field exists
        patients = users.filter(role='patient')  # Assuming 'role' field exists

        # Serialize the data
        doctor_data = [
            {"id": doctor.id, "first_name": doctor.first_name, "last_name": doctor.last_name, "email": doctor.email}
            for doctor in doctors
        ]
        patient_data = [
            {"id": patient.id, "first_name": patient.first_name, "last_name": patient.last_name, "email": patient.email}
            for patient in patients
        ]

        return Response(
            {"doctors": doctor_data, "patients": patient_data},
            status=status.HTTP_200_OK
        )