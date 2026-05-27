"""
Docker Compose 로컬 실행용.

`production` 과 동일하게 PostgreSQL·환경변수 기반으로 두고,
컨테이너에서 HTTP로 접속할 때 세션/CSRF 보안 플래그만 완화한다.

    DJANGO_SETTINGS_MODULE=config.settings.docker
"""
from decouple import config

from ._hosts import build_allowed_hosts
from .production import *

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = build_allowed_hosts(
    config('ALLOWED_HOSTS', default='localhost,127.0.0.1,web,0.0.0.0')
)

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
