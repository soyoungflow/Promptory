from django.urls import path

from . import blueprint_views, views

urlpatterns = [
    path('blueprints/design/', blueprint_views.BlueprintDesignListCreateView.as_view(), name='blueprint-design-list'),
    path('blueprints/design/<int:pk>/', blueprint_views.BlueprintDesignDetailView.as_view(), name='blueprint-design-detail'),
    path(
        'blueprints/design/<int:pk>/publish-recipe/',
        blueprint_views.BlueprintPublishRecipeView.as_view(),
        name='blueprint-publish-recipe',
    ),
    path('prompts/<int:pk>/transform/', views.TransformPromptView.as_view(), name='prompt-transform'),
    path('prompts/<int:pk>/agent/', views.AgentDetailView.as_view(), name='prompt-agent'),
    path('prompts/<int:pk>/similar/', views.SimilarPromptsView.as_view(), name='prompt-similar'),
    path('tasks/<uuid:task_id>/status/', views.TaskStatusView.as_view(), name='task-status'),
]
