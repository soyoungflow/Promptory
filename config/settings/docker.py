"""
Docker Compose 로컬 실행용.

`production` 과 동일하게 PostgreSQL·환경변수 기반으로 두고,
컨테이너에서 HTTP로 접속할 때 세션/CSRF 보안 플래그만 완화한다.

    DJANGO_SETTINGS_MODULE=config.settings.docker
"""
import os
import sys

# Celery multiproc env는 web/daphne·migrate에서 django-prometheus와 충돌한다.
# django_prometheus AppConfig.ready() 보다 먼저 제거해야 한다.
_argv = ' '.join(sys.argv)
if not ('celery' in _argv and 'worker' in _argv):
    os.environ.pop('PROMETHEUS_MULTIPROC_DIR', None)

from decouple import config

from ._hosts import build_allowed_hosts
from .production import *

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = build_allowed_hosts(
    config('ALLOWED_HOSTS', default='localhost,127.0.0.1,web,0.0.0.0')
)

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
