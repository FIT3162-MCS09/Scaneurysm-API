from django.db import models
from src.models.user import User
class DoctorManager(models.Manager):
    def create_doctor(self, username, email, license_number, specialty, **extra_fields):
        user = User.objects.create_user(username, email, role='doctor', **extra_fields)
        doctor = self.model(user=user, license_number=license_number, specialty=specialty)
        user.save(using=self._db)
        return doctor
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    license_number = models.CharField(max_length=255, unique=True)
    specialty = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.license_number} - {self.specialty}"
    
    class Meta:
        db_table = 'doctors'