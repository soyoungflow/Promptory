"""
Custom Manager — Soft Delete 처리.

기본 QuerySet에서 is_deleted=True 항목을 자동으로 제외.
관리자 페이지에서는 전체를 볼 수 있도록 all_objects도 제공.
"""
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        """삭제되지 않은 항목만"""
        return self.filter(is_deleted=False)

    def deleted(self):
        """삭제된 항목만"""
        return self.filter(is_deleted=True)

    def soft_delete(self, user=None):
        """QuerySet 일괄 Soft Delete"""
        return self.update(
            is_deleted=True,
            deleted_at=timezone.now(),
            deleted_by=user,
        )

    def restore(self):
        """QuerySet 일괄 복구"""
        return self.update(
            is_deleted=False,
            deleted_at=None,
            deleted_by=None,
        )


class SoftDeleteManager(models.Manager):
    """기본 Manager — is_deleted=False 항목만 반환"""
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def alive(self):
        return self.get_queryset()

    def deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()

    def all_with_deleted(self):
        """관리자용 — 삭제 포함 전체"""
        return SoftDeleteQuerySet(self.model, using=self._db)
