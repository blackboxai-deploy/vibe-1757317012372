from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        """Initialize AI models and indices on app startup."""
        try:
            from .ai_services import initialize_ai_services
            initialize_ai_services()
        except Exception as e:
            print(f"Warning: Could not initialize AI services: {e}")
            print("The application will run with fallback responses.")