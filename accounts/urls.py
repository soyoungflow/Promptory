from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, LogoutView, MeView, MyPromptListView, MyTransformationListView
from interaction.views import MyBookmarkListView, MyLikedPromptListView, MyCommentListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),       # JWT 발급
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('me/prompts/', MyPromptListView.as_view(), name='my-prompts'),
    path('me/transformations/', MyTransformationListView.as_view(), name='my-transformations'),
    path('me/bookmarks/', MyBookmarkListView.as_view(), name='my-bookmarks'),
    path('me/likes/', MyLikedPromptListView.as_view(), name='my-likes'),
    path('me/comments/', MyCommentListView.as_view(), name='my-comments'),
]
