from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── DRF API (데이터 처리 전용) ──
    path('api/accounts/', include('accounts.urls')),
    path('api/prompts/',  include('prompts.urls')),
    path('api/',          include('interaction.urls')),

    # ── Template Views (화면 렌더링 전용) ──
    path('accounts/', include('accounts.template_urls')),
    path('', include('prompts.template_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
