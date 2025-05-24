from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.permissions import IsAuthenticated


from ..serializers.sign_up_serializer import PatientSerializer, DoctorSerializer
from ..service.search_service import SearchService
from models.patient import Patient
from models.doctor import Doctor

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
            # Use search service to fetch the patient
            patient = SearchService.search_patient_by_user_id(user_id)
            serializer = PatientSerializer(patient)
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
            # Use search service to fetch the doctor
            doctor = SearchService.search_doctor_by_user_id(user_id)
            serializer = DoctorSerializer(doctor)
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

        try:
            # Use search service to fetch users
            doctors_data, patients_data = SearchService.search_users(
                first_name=first_name,
                last_name=last_name,
                email=email
            )

            if not doctors_data and not patients_data:
                return Response({"error": "No users found"}, status=status.HTTP_404_NOT_FOUND)

            return Response(
                {"doctors": doctors_data, "patients": patients_data},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DoctorPatientsView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        parameters=[
            OpenApiParameter(name='doctor_id', description='ID of the doctor (must match the authenticated user)', required=True, type=str)
        ],
        responses={
            200: OpenApiResponse(
                description="List of patients for the doctor",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "user_id": {"type": "integer"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "email": {"type": "string"},
                            "date_of_birth": {"type": "string", "format": "date"},
                            "gender": {"type": "string"},
                            "blood_type": {"type": "string"}
                        }
                    }
                }
            ),
            404: OpenApiResponse(
                description="Doctor not found",
                response={"type": "object", "properties": {"error": {"type": "string"}}}
            ),
            403: OpenApiResponse(
                description="Permission denied",
                response={"type": "object", "properties": {"error": {"type": "string"}}}
            )
        }
    )
    def get(self, request, *args, **kwargs):
        # Get the logged-in user's ID from the JWT token
        logged_in_user_id = str(request.user.id)
        
        # Get the requested doctor_id from query params
        doctor_id = request.query_params.get('doctor_id')
        
        # Verify the logged-in user is requesting their own patients
        if doctor_id != logged_in_user_id:
            return Response(
                {"error": "You can only view your own patients"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patients = SearchService.search_doctor_patients(doctor_id)
            return Response(patients, status=status.HTTP_200_OK)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)