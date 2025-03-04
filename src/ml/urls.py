from django.urls import path

from api.views import PredictionView

urlpatterns = [
    path('predict/', PredictionView.as_view(), name='predict'),
]