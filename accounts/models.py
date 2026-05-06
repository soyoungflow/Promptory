from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    확장된 사용자 모델.
    AbstractUser 상속으로 기본 인증 기능 그대로 유지.
    AUTH_USER_MODEL = 'accounts.CustomUser' 로 등록됨.
    """
    email = models.EmailField(unique=True, verbose_name='이메일')
    bio = models.TextField(blank=True, verbose_name='자기소개')
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='프로필 이미지',
    )

    # Soft Delete
    is_deleted = models.BooleanField(default=False, verbose_name='탈퇴 여부')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='탈퇴 일시')

    # username 대신 email을 로그인 식별자로 사용
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # createsuperuser 시 추가 입력

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'

    def __str__(self):
        return self.email

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False  # 로그인 차단
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])
