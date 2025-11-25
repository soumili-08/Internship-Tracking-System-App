from django.apps import AppConfig


class ApplicationTrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'application_tracking'


from django.apps import AppConfig

class ApplicationTrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'application_tracking'

    def ready(self):
        from django.db.utils import OperationalError
        from .models import TestCategory

        default_categories = ["Math", "Aptitude", "English", "Coding"]
        try:
            for name in default_categories:
                TestCategory.objects.get_or_create(name=name)
        except OperationalError:
            # Database might not be ready during first migrate
            pass

