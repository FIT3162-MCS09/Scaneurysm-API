from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from models.user import User
from models.patient import Patient
from models.doctor import Doctor


class UserSerializer(serializers.ModelSerializer):
    hashed_password = serializers.CharField(write_only=True)  # Ensure password is write-only

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'hashed_password']

    def create(self, validated_data):
        # Extract and hash the password before saving the user
        hashed_password = validated_data.pop('hashed_password')
        validated_data['hashed_password'] = make_password(hashed_password)
        # Create the User object
        user = User.objects.create(**validated_data)

        return user


class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Patient
        fields = ['user', 'medical_record_number']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        patient = Patient.objects.create(user=user, **validated_data)
        return patient


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Doctor
        fields = ['user', 'license_number', 'specialty']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        doctor = Doctor.objects.create(user=user, **validated_data)
        return doctor