import sys

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'

    def ready(self):
        # Celery worker는 prefork + multiprocess로 메트릭을 노출한다.
        # 부모 프로세스에서 등록하면 자식과 registry가 어긋나므로 web/daphne만 등록한다.
        argv = ' '.join(sys.argv)
        if 'celery' in argv and 'worker' in argv:
            return
        from . import metrics  # noqa: F401 — register custom counters on web /metrics
