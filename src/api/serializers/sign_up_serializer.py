from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from models.user import User
from models.patient import Patient
from models.doctor import Doctor


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Ensure password is write-only

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role']

    def create(self, validated_data):
        # Extract and hash the password before saving the user
        password = validated_data.pop('password')
        validated_data['password'] = make_password(password)
        # Create the User object
        user = User.objects.create(**validated_data)

        return user


class PatientSerializer(serializers.ModelSerializer):
    # Flatten the user fields
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = Patient
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 
                  'medical_record_number', 'birth_date', 'sex', 'primary_doctor']
    
    def create(self, validated_data):
        # Extract user fields
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'password': validated_data.pop('password'),
            'role': 'patient'
        }
        
        # Create user first
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        
        # Create patient
        patient = Patient.objects.create(user=user, **validated_data)
        return patient


class DoctorSerializer(serializers.ModelSerializer):
    # Flatten the user fields
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = Doctor
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 
                  'license_number', 'specialty']
    
    def create(self, validated_data):
        # Extract user fields
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'password': validated_data.pop('password'),
            'role': 'doctor'
        }
        
        # Create user first
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        
        # Create doctor
        doctor = Doctor.objects.create(user=user, **validated_data)
        return doctor