from .base import *
from decouple import config

DEBUG = True

# 로컬 개발: PostgreSQL (.env 에 없으면 아래 기본값 — Postgres 에 DB·유저가 맞춰져 있어야 함)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='promptory_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 5,
        },
    }
}
