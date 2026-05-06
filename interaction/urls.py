from django.urls import path
from .views import CommentListCreateView, CommentDeleteView, LikeToggleView, BookmarkToggleView

urlpatterns = [
    path('prompts/<int:prompt_id>/comments/', CommentListCreateView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', CommentDeleteView.as_view(), name='comment-delete'),
    path('prompts/<int:prompt_id>/like/', LikeToggleView.as_view(), name='like-toggle'),
    path('prompts/<int:prompt_id>/bookmark/', BookmarkToggleView.as_view(), name='bookmark-toggle'),
]
