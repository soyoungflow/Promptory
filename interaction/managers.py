from django.db import models
from django.utils import timezone


class CommentManager(models.Manager):
    """살아있는 댓글만 (is_deleted=False)"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super().get_queryset()
