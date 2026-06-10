import os

# daphne 전용 — Celery multiproc env가 있으면 django-prometheus 기동 실패
os.environ.pop('PROMETHEUS_MULTIPROC_DIR', None)

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from tasks.middleware import JwtAuthMiddleware  # noqa: E402
from tasks.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': JwtAuthMiddleware(URLRouter(websocket_urlpatterns)),
})
