import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Prompt


@receiver(post_save, sender=Prompt)
def enqueue_embed_on_create(sender, instance, created, **kwargs):
    import sys

    if 'test' in sys.argv or not created or instance.is_deleted:
        return
    from tasks.celery_tasks import embed_prompt
    from tasks.models import Task

    task = Task.objects.create(
        task_id=uuid.uuid4(),
        task_type='embed',
        status='PENDING',
        prompt=instance,
        user=instance.user,
    )
    try:
        embed_prompt.delay(str(task.task_id), instance.id)
    except Exception:
        Task.objects.filter(pk=task.pk).update(
            status='FAIL',
            error_message='Celery broker unavailable',
            finished_at=timezone.now(),
        )
