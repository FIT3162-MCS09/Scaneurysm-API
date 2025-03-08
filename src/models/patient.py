from django.db import models
from .user import User
class PatientManager(models.Manager):
    def create_patient(self, username, email, medical_record_number, **extra_fields):
        user = User.objects.create_user(username, email, role='patient', **extra_fields)
        patient = self.model(user=user, medical_record_number=medical_record_number)
        user.save(using=self._db)
        return patient
class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    medical_record_number = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.medical_record_number}"
    
    class Meta:
        db_table = 'patients'