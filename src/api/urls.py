from django.urls import path
from .views.auth_view import PatientSignUpView, DoctorSignUpView, SignInView

urlpatterns = [
    path('signup/patient/', PatientSignUpView.as_view(), name='signup_patient'),
    path('signup/doctor/', DoctorSignUpView.as_view(), name='signup_doctor'),
    path('signin/', SignInView.as_view(), name='signin'),
]