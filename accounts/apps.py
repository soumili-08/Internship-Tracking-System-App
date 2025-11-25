from django.apps import AppConfig
from django.db.utils import OperationalError

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Import models here to avoid early database access
        from .models import User
        try:
            if not User.objects.filter(role='admin').exists():
                User.objects.create_user(
                    email='soumili@gmail.com',
                    password='malda',
                    role='admin'
                )
                print("Default admin created")
        except OperationalError:
            # Database tables might not be ready during initial migrations
            pass
