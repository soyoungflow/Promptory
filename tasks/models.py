import uuid

from django.conf import settings
from django.db import models


class Task(models.Model):
    STATUS_CHOICES = [
        ('PENDING', '대기'),
        ('PROCESSING', '처리 중'),
        ('SUCCESS', '성공'),
        ('FAIL', '실패'),
    ]
    TASK_TYPE_CHOICES = [
        ('transform', '에이전트 변환'),
        ('blueprint_design', '설계서 만들기'),
        ('embed', '임베딩'),
    ]

    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    prompt = models.ForeignKey('prompts.Prompt', on_delete=models.CASCADE, related_name='tasks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_tasks')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default='')
    result_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['prompt', 'task_type']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f'{self.task_id} ({self.status})'
