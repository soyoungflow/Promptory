import glob
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest, multiprocess

from monitoring.multiproc import CELERY_MULTIPROC_DIR

METRICS_PORT = int(os.environ.get('CELERY_METRICS_PORT', '9100'))


def _multiproc_dir() -> str:
    return CELERY_MULTIPROC_DIR


def _clean_multiproc_dir() -> None:
    directory = _multiproc_dir()
    os.makedirs(directory, exist_ok=True)
    for path in glob.glob(os.path.join(directory, '*')):
        if os.path.isfile(path):
            os.remove(path)


class _MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/metrics':
            self.send_response(404)
            self.end_headers()
            return

        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        output = generate_latest(registry)
        self.send_response(200)
        self.send_header('Content-Type', CONTENT_TYPE_LATEST)
        self.end_headers()
        self.wfile.write(output)

    def log_message(self, _format, *_args):
        return


def start_celery_metrics_server() -> None:
    os.environ['PROMETHEUS_MULTIPROC_DIR'] = CELERY_MULTIPROC_DIR
    os.makedirs(CELERY_MULTIPROC_DIR, exist_ok=True)
    _clean_multiproc_dir()
    httpd = HTTPServer(('0.0.0.0', METRICS_PORT), _MetricsHandler)
    thread = Thread(target=httpd.serve_forever, daemon=True, name='celery-metrics')
    thread.start()
