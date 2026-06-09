import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from ai_gateway.models import AgentTransformation, PromptEmbedding
from prompts.models import Category, Prompt
from tasks.celery_tasks import embed_prompt, transform_prompt
from tasks.models import Task

User = get_user_model()

MOCK_TRANSFORM = {
    'decomposed_steps': [
        {'step': 1, 'name': '리서치', 'system_message': '조사', 'tool': 'web_search'},
        {'step': 2, 'name': '초안', 'system_message': '작성', 'tool': 'text_generation'},
        {'step': 3, 'name': '검토', 'system_message': '검토', 'tool': 'reflection'},
        {'step': 4, 'name': '완료', 'system_message': '마무리', 'tool': 'outline_generator'},
    ],
    'suggested_tools': ['web_search'],
    'system_messages': ['조사', '작성', '검토', '마무리'],
    'confidence_score': 0.92,
    'model_used': 'mock',
}

MOCK_EMBED = {
    'vector': [0.1, 0.2, 0.3],
    'dim': 3,
    'model_name': 'mock',
}


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class TransformTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='celery@example.com', username='celery', password='StrongPass123!',
        )
        self.category = Category.objects.create(name='개발', slug='dev')
        self.prompt = Prompt.objects.create(
            user=self.user,
            category=self.category,
            title='Celery 변환 테스트',
            content='변환할 프롬프트 본문입니다.',
            ai_model='gpt-5-5',
        )
        self.task = Task.objects.create(
            task_id=uuid.uuid4(),
            task_type='transform',
            status='PENDING',
            prompt=self.prompt,
            user=self.user,
        )

    @patch('tasks.celery_tasks.notify_task_status')
    @patch('tasks.celery_tasks.LLMClient')
    def test_transform_task_success(self, mock_client_cls, _mock_notify):
        mock_client_cls.return_value.transform.return_value = MOCK_TRANSFORM

        result_id = transform_prompt(str(self.task.task_id), self.prompt.id)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'SUCCESS')
        self.assertEqual(self.task.result_id, result_id)
        transformation = AgentTransformation.objects.get(pk=result_id)
        self.assertEqual(len(transformation.decomposed_steps), 4)
        self.assertEqual(transformation.model_used, 'mock')

    @patch('tasks.celery_tasks.notify_task_status')
    @patch('tasks.celery_tasks.LLMClient')
    def test_transform_task_fails_on_empty_steps(self, mock_client_cls, _mock_notify):
        mock_client_cls.return_value.transform.return_value = {
            **MOCK_TRANSFORM,
            'decomposed_steps': [],
        }

        def _no_retry(**kwargs):
            raise kwargs['exc']

        with patch.object(transform_prompt, 'retry', side_effect=_no_retry):
            with self.assertRaises(ValueError):
                transform_prompt(str(self.task.task_id), self.prompt.id)

        self.task.refresh_from_db()
        self.assertIn('워크플로', self.task.error_message)
        self.assertFalse(AgentTransformation.objects.filter(prompt=self.prompt).exists())


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class EmbedTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='embed@example.com', username='embed', password='StrongPass123!',
        )
        self.category = Category.objects.create(name='개발', slug='dev')
        self.prompt = Prompt.objects.create(
            user=self.user,
            category=self.category,
            title='임베딩 테스트',
            content='임베딩 본문',
            ai_model='gpt-5-5',
        )
        self.task = Task.objects.create(
            task_id=uuid.uuid4(),
            task_type='embed',
            status='PENDING',
            prompt=self.prompt,
            user=self.user,
        )

    @patch('tasks.celery_tasks.notify_task_status')
    @patch('tasks.celery_tasks.LLMClient')
    def test_embed_task_success(self, mock_client_cls, _mock_notify):
        mock_client_cls.return_value.embed.return_value = MOCK_EMBED

        result_id = embed_prompt(str(self.task.task_id), self.prompt.id)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'SUCCESS')
        self.assertEqual(self.task.result_id, result_id)
        embedding = PromptEmbedding.objects.get(prompt=self.prompt)
        self.assertEqual(embedding.vector, MOCK_EMBED['vector'])
