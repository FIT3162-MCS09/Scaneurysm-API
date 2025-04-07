from django.urls import path, include
from .views.file_view import FileUploadView, UserFilesView
from .views.auth_view import (
    PatientSignUpView, 
    DoctorSignUpView, 
    SignInView,
    LogoutView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views.health_view import HealthView
from .views.protected_view import ProfileView  # Assuming you implemented this
from .views.search_view import PatientSearchView, UserSearchView, DoctorSearchView
# Group URL patterns by feature/functionality
urlpatterns = [
    # Authentication endpoints
    path('auth/', include([
        path('signup/patient/', PatientSignUpView.as_view(), name='signup_patient'),
        path('signup/doctor/', DoctorSignUpView.as_view(), name='signup_doctor'),
        path('signin/', SignInView.as_view(), name='signin'),
        path('logout/', LogoutView.as_view(), name='logout'),
        path('profile/', ProfileView.as_view(), name='profile'),
    ])),

    path('search/', include([
        path('user/', UserSearchView.as_view(), name='search user'),
        path('patient/', PatientSearchView.as_view(), name='search patient'),
        path('doctor/', DoctorSearchView.as_view(), name='search doctor')
    ])),
    
    # File management endpoints
    path('files/', include([
        path('upload/', FileUploadView.as_view(), name='file-upload'),
        path('view/', UserFilesView.as_view(), name='user-files'),
    ])),
    
    # System endpoints
    path('system/', include([
        path('health/', HealthView.as_view(), name='health'),
    ])),

    path('jwt/', include([
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ])),
]