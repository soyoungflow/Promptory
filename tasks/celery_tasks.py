import time

import structlog
from celery import shared_task
from django.utils import timezone

from ai_gateway.models import AgentTransformation, PromptEmbedding
from ai_gateway.services.llm_client import LLMClient
from monitoring.metrics import agent_transformation_total, model_inference_duration_seconds
from prompts.models import Prompt
from tasks.models import Task
from tasks.task_notify import notify_task_status

logger = structlog.get_logger()


def _set_status(task: Task, status: str, **extra) -> None:
    task.status = status
    update_fields = ['status']
    for key, value in extra.items():
        setattr(task, key, value)
        update_fields.append(key)
    task.save(update_fields=update_fields)
    notify_task_status(task)


@shared_task(bind=True, max_retries=3, default_retry_delay=2)
def transform_prompt(self, task_id: str, prompt_id: int):
    task = Task.objects.get(task_id=task_id)
    _set_status(task, 'PROCESSING', started_at=timezone.now())
    logger.info('transform_started', task_id=str(task_id), prompt_id=prompt_id)

    try:
        prompt = Prompt.objects.get(pk=prompt_id, is_deleted=False)
        started = time.time()
        result = LLMClient().transform(prompt.content)
        elapsed = time.time() - started

        model_inference_duration_seconds.labels(
            model=result.get('model_used', 'unknown'),
            task_type='transform',
        ).observe(elapsed)

        steps = result.get('decomposed_steps', [])
        transformation = AgentTransformation.objects.create(
            prompt=prompt,
            decomposed_steps=steps,
            suggested_tools=result.get('suggested_tools', []),
            system_messages=result.get('system_messages', []),
            confidence_score=float(result.get('confidence_score', 0.0)),
            model_used=result.get('model_used', ''),
        )

        agent_transformation_total.labels(
            status='SUCCESS',
            model_used=result.get('model_used', 'unknown'),
        ).inc()

        _set_status(
            task,
            'SUCCESS',
            finished_at=timezone.now(),
            result_id=transformation.id,
            error_message='',
        )
        logger.info('transform_success', task_id=str(task_id), result_id=transformation.id)
        return transformation.id

    except Exception as exc:
        agent_transformation_total.labels(status='FAIL', model_used='unknown').inc()
        task.error_message = str(exc)[:500]
        task.save(update_fields=['error_message'])
        logger.error('transform_failed', task_id=str(task_id), error=str(exc))

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)

        _set_status(task, 'FAIL', finished_at=timezone.now())
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=2)
def embed_prompt(self, task_id: str, prompt_id: int):
    task = Task.objects.get(task_id=task_id)
    _set_status(task, 'PROCESSING', started_at=timezone.now())

    try:
        prompt = Prompt.objects.get(pk=prompt_id, is_deleted=False)
        text = f'{prompt.title}\n{prompt.description}\n{prompt.content}'[:5000]
        started = time.time()
        payload = LLMClient().embed(text)
        elapsed = time.time() - started

        model_inference_duration_seconds.labels(
            model=payload.get('model_name', 'unknown'),
            task_type='embed',
        ).observe(elapsed)

        embedding, _created = PromptEmbedding.objects.update_or_create(
            prompt=prompt,
            defaults={
                'vector': payload['vector'],
                'model_name': payload.get('model_name', ''),
            },
        )

        _set_status(
            task,
            'SUCCESS',
            finished_at=timezone.now(),
            result_id=embedding.id,
            error_message='',
        )
        return embedding.id

    except Exception as exc:
        task.error_message = str(exc)[:500]
        task.save(update_fields=['error_message'])

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)

        _set_status(task, 'FAIL', finished_at=timezone.now())
        raise
