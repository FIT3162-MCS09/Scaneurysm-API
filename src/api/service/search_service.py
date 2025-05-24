from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from rest_framework.exceptions import PermissionDenied

class SearchService:
    @staticmethod
    def search_patient_by_user_id(user_id):
        """
        Search for a patient by user_id
        """
        return Patient.objects.get(user_id=user_id)

    @staticmethod
    def search_doctor_by_user_id(user_id):
        """
        Search for a doctor by user_id
        """
        return Doctor.objects.get(user_id=user_id)

    @staticmethod
    def search_users(first_name=None, last_name=None, email=None):
        """
        Search for users based on first name, last name, and/or email
        """
        filters = {}
        if first_name:
            filters['first_name__icontains'] = first_name
        if last_name:
            filters['last_name__icontains'] = last_name
        if email:
            filters['email__icontains'] = email

        if not filters:
            raise ValueError("At least one search parameter (first_name, last_name, or email) is required")

        users = User.objects.filter(**filters)
        if not users.exists():
            return [], []

        # Divide users into doctors and patients
        doctors = users.filter(role='doctor')
        patients = users.filter(role='patient')

        # Format the data
        doctor_data = [
            {"id": doctor.id, "first_name": doctor.first_name, "last_name": doctor.last_name, "email": doctor.email}
            for doctor in doctors
        ]
        patient_data = [
            {"id": patient.id, "first_name": patient.first_name, "last_name": patient.last_name, "email": patient.email}
            for patient in patients
        ]

        return doctor_data, patient_data

    @staticmethod
    def search_doctor_patients(doctor_id):
        """
        Search for all patients linked to a specific doctor
        Args:
            doctor_id: The user_id of the doctor
        Returns:
            List of patient data
        Raises:
            Doctor.DoesNotExist: If doctor is not found
            PermissionDenied: If user is not a doctor
        """
        # Verify the doctor exists and is actually a doctor
        try:
            doctor = Doctor.objects.get(user_id=doctor_id)
            if not doctor.user.role == 'doctor':
                raise PermissionDenied("Only doctors can access their patient list")
                
            # Get all patients linked to this doctor
            patients = Patient.objects.filter(primary_doctor=doctor)
            
            # Format the patient data
            patient_data = [
                {
                    "user_id": patient.user_id,  # Using user_id directly
                    "first_name": patient.user.first_name,
                    "last_name": patient.user.last_name,
                    "email": patient.user.email,
                    "birth_date": patient.birth_date,
                    "sex": patient.sex,
                    "medical_record_number": patient.medical_record_number
                }
                for patient in patients
            ]
            
            return patient_data
        except Doctor.DoesNotExist:
            raise Doctor.DoesNotExist("Doctor not found")