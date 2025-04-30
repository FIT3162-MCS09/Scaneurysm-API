from django.db import models
from src.models.user import User
from src.models.doctor import Doctor
class PatientManager(models.Manager):
    def create_patient(self, username, email, medical_record_number, **extra_fields):
        user = User.objects.create_user(username, email, role='patient', **extra_fields)
        patient = self.model(user=user, medical_record_number=medical_record_number)
        user.save(using=self._db)
        return patient
class Patient(models.Model):
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('I', 'Intersex'),
        ('O', 'Other'),
        ('U', 'Unspecified'),
        ('P', 'Prefer Not To Say')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    medical_record_number = models.CharField(max_length=255, unique=True)
    birth_date = models.DateField(null=False, blank=False)
    sex = models.CharField(max_length=7, choices=SEX_CHOICES)
    primary_doctor = models.ForeignKey(
                    Doctor,
                    on_delete=models.SET_NULL,  # or CASCADE, PROTECT, etc. depending on your needs
                    null=True,
                    blank=True,  # if having a primary doctor is optional
                    related_name='patients'  # to access patient list from doctor instance
                )

    def __str__(self):
        return f"{self.user.username} - {self.medical_record_number}"
    
    class Meta:
        db_table = 'patients'