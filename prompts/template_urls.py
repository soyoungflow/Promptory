from django.urls import path
from . import template_views

urlpatterns = [
    path('', template_views.home, name='home-page'),
    path('library/', template_views.library, name='library-page'),
    path('prompts/', template_views.prompt_list, name='prompt-list-page'),
    path('prompts/<int:pk>/', template_views.prompt_detail, name='prompt-detail-page'),
    path('prompts/new/', template_views.prompt_create, name='prompt-create-page'),
    path('prompts/<int:pk>/edit/', template_views.prompt_edit, name='prompt-edit-page'),
]
