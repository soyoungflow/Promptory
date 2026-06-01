from django.urls import path

from . import views

urlpatterns = [
    path('prompts/<int:pk>/transform/', views.TransformPromptView.as_view(), name='prompt-transform'),
    path('prompts/<int:pk>/agent/', views.AgentDetailView.as_view(), name='prompt-agent'),
    path('prompts/<int:pk>/similar/', views.SimilarPromptsView.as_view(), name='prompt-similar'),
    path('tasks/<uuid:task_id>/status/', views.TaskStatusView.as_view(), name='task-status'),
]
