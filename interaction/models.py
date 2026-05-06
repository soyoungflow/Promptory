from django.db import models
from django.conf import settings
from django.utils import timezone
from .managers import CommentManager


class Comment(models.Model):
    prompt = models.ForeignKey('prompts.Prompt', on_delete=models.CASCADE,
                               related_name='comments', verbose_name='프롬프트')
    user   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='comments', verbose_name='작성자')
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               null=True, blank=True,
                               related_name='replies', verbose_name='부모 댓글')
    content    = models.TextField(verbose_name='내용')
    is_deleted = models.BooleanField(default=False, db_index=True, verbose_name='삭제 여부')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='삭제 일시')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    objects     = CommentManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name        = '댓글'
        verbose_name_plural = '댓글 목록'
        ordering            = ['created_at']

    def __str__(self):
        prefix = '↳ ' if self.parent else ''
        return f"{prefix}{self.user.email}: {self.content[:30]}"

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    @property
    def is_reply(self):
        return self.parent is not None


class Like(models.Model):
    prompt     = models.ForeignKey('prompts.Prompt', on_delete=models.CASCADE,
                                   related_name='likes', verbose_name='프롬프트')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='likes', verbose_name='사용자')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '좋아요'
        verbose_name_plural = '좋아요 목록'
        unique_together     = ('prompt', 'user')

    def __str__(self):
        return f"{self.user.email} ♥ {self.prompt.title}"


class Bookmark(models.Model):
    prompt     = models.ForeignKey('prompts.Prompt', on_delete=models.CASCADE,
                                   related_name='bookmarks', verbose_name='프롬프트')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='bookmarks', verbose_name='사용자')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '북마크'
        verbose_name_plural = '북마크 목록'
        unique_together     = ('prompt', 'user')

    def __str__(self):
        return f"{self.user.email} 🔖 {self.prompt.title}"
