from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Arryn_Back.infrastructure.api'  # ruta completa del paquete
    label = 'api'  