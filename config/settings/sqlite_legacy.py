"""
기존 SQLite(db.sqlite3)에서만 데이터를 덤프할 때 사용.

    DJANGO_SETTINGS_MODULE=config.settings.sqlite_legacy \\
      python manage.py dumpdata ...

운영/로컬 기본 설정은 `local.py`(PostgreSQL)를 사용한다.
"""
from .base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
