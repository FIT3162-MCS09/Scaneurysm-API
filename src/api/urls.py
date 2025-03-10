from django.urls import path

from .views.file_view import FileUploadView, UserFilesView
from .views.auth_view import PatientSignUpView, DoctorSignUpView, SignInView

urlpatterns = [
    path('signup/patient/', PatientSignUpView.as_view(), name='signup_patient'),
    path('signup/doctor/', DoctorSignUpView.as_view(), name='signup_doctor'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('files/', UserFilesView.as_view(), name='user-files'),
]