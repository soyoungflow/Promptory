"""settings 진입점.

- 로컬 개발: local
- 배포/운영(Vercel 포함): production
"""
import os

_is_vercel = os.environ.get('VERCEL') == '1'
_is_production = os.environ.get('DJANGO_ENV', '').lower() == 'production'

if _is_vercel or _is_production:
    from .production import *  # noqa: F401,F403
else:
    from .local import *  # noqa: F401,F403
