import os
import sys

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'

    def ready(self):
        argv = ' '.join(sys.argv)
        if 'celery' in argv and 'worker' in argv:
            return
        # Celery용 multiprocess env가 web/daphne에 섞이면 django-prometheus가 기동 실패함.
        # (compose·호스트 env 유입 방어 — middleware 로드 전에 제거)
        os.environ.pop('PROMETHEUS_MULTIPROC_DIR', None)
        from . import metrics  # noqa: F401 — register custom counters on web /metrics
