from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notify_task_status(task) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f'user_{task.user_id}',
        {
            'type': 'task.update',
            'data': {
                'task_id': str(task.task_id),
                'status': task.status,
                'task_type': task.task_type,
                'prompt_id': task.prompt_id,
                'error_message': task.error_message or '',
            },
        },
    )
