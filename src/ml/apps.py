from django.apps import AppConfig

class MLConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml'

    def ready(self):
        # Import and initialize ModelService when Django starts
        from .model_service import ModelService
        ModelService()