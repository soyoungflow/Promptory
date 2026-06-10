import os

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown, worker_ready

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('PROMETHEUS_MULTIPROC_DIR', '/tmp/prometheus_multiproc')

app = Celery('promptory')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@worker_process_init.connect
def init_celery_prometheus(**_kwargs):
    """Prefork 자식 프로세스에서 multiprocess 메트릭 모드 활성화."""
    multiproc_dir = os.environ['PROMETHEUS_MULTIPROC_DIR']
    os.makedirs(multiproc_dir, exist_ok=True)
    from prometheus_client import values
    from prometheus_client.values import MultiProcessValue

    values.ValueClass = MultiProcessValue()


@worker_ready.connect
def start_celery_metrics_endpoint(**_kwargs):
    from monitoring.metrics_server import start_celery_metrics_server

    start_celery_metrics_server()


@worker_process_shutdown.connect
def shutdown_celery_prometheus(**_kwargs):
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(os.getpid())
