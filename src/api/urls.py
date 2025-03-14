from django.urls import path

from .views.file_view import FileUploadView, UserFilesView
from .views.auth_view import PatientSignUpView, DoctorSignUpView, SignInView
from .views.health_view import HealthView

urlpatterns = [
    path('signup/patient/', PatientSignUpView.as_view(), name='signup_patient'),
    path('signup/doctor/', DoctorSignUpView.as_view(), name='signup_doctor'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('files/upload/', FileUploadView.as_view(), name='file-upload'),
    path('files/view', UserFilesView.as_view(), name='user-files'),
    path('health-check/', HealthView.as_view(), name='health'),
]