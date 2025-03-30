from django.apps import AppConfig

class VotingAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Auto field for primary keys
    name = 'voting_app'  # Name of your application

    def ready(self):
        from . import face_recognition