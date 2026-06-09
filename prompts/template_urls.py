from django.urls import path
from . import template_views

urlpatterns = [
    path('', template_views.home, name='home-page'),
    path('blueprints/new/', template_views.blueprint_design, name='blueprint-design-page'),
    path('blueprints/<int:pk>/', template_views.blueprint_design, name='blueprint-design-detail-page'),
    path('library/', template_views.library, name='library-page'),
    path('prompts/', template_views.prompt_list, name='prompt-list-page'),
    path('prompts/<int:pk>/', template_views.prompt_detail, name='prompt-detail-page'),
    path('prompts/new/', template_views.prompt_create, name='prompt-create-page'),
    path('prompts/<int:pk>/edit/', template_views.prompt_edit, name='prompt-edit-page'),
]
