from django.urls import path

from src.api.views.prediction_view import PredictionView

urlpatterns = [
    path('predict/', PredictionView.as_view(), name='predict'),
]