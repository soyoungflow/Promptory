from django.urls import path
from . import template_views

urlpatterns = [
    path('login/', template_views.login_page, name='login-page'),
    path('register/', template_views.register_page, name='register-page'),
]
