import glob
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest, multiprocess

METRICS_PORT = int(os.environ.get('CELERY_METRICS_PORT', '9100'))
MULTIPROC_DIR = os.environ.get('PROMETHEUS_MULTIPROC_DIR', '/tmp/prometheus_multiproc')


def _clean_multiproc_dir() -> None:
    os.makedirs(MULTIPROC_DIR, exist_ok=True)
    for path in glob.glob(os.path.join(MULTIPROC_DIR, '*')):
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
    _clean_multiproc_dir()
    httpd = HTTPServer(('0.0.0.0', METRICS_PORT), _MetricsHandler)
    thread = Thread(target=httpd.serve_forever, daemon=True, name='celery-metrics')
    thread.start()
