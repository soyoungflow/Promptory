"""
운영 환경 설정 — PostgreSQL 사용.

전환 체크포인트 (조건서 기준):
1. .env 로 DB 설정 분리  ✅
2. settings.py DB 설정 분리  ✅ (local.py / production.py)
3. migration 파일 정리  → migrate 실행 전 확인
4. PostgreSQL 연결  ✅ (아래 설정)
5. migrate 실행  → python manage.py migrate
6. 기존 기능 E2E 정상 동작 확인  → 수동 테스트
"""
from .base import *
from decouple import config

from ._hosts import build_allowed_hosts

DEBUG = config('DEBUG', default=False, cast=bool)
if config('VERCEL', default='0') == '1':
    DEBUG = False

ALLOWED_HOSTS = build_allowed_hosts(config('ALLOWED_HOSTS', default=''))

# ── PostgreSQL ──
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     config('DB_NAME'),
        'USER':     config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST':     config('DB_HOST', default='localhost'),
        'PORT':     config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 5,
        },
    }
}

# 운영 보안 설정
SECURE_BROWSER_XSS_FILTER   = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS             = 'DENY'
SESSION_COOKIE_SECURE       = True
CSRF_COOKIE_SECURE          = True
