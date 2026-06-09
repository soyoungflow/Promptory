from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'

    def ready(self):
        from . import metrics  # noqa: F401 — register custom counters on web /metrics
