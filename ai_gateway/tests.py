import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from ai_gateway.models import AgentTransformation, BlueprintDesign, PromptEmbedding
from prompts.models import Category, Prompt
from tasks.models import Task

User = get_user_model()

MOCK_TRANSFORM = {
    'decomposed_steps': [
        {'step': 1, 'name': '리서치', 'system_message': '조사하세요.', 'tool': 'web_search'},
        {'step': 2, 'name': '초안', 'system_message': '작성하세요.', 'tool': 'text_generation'},
    ],
    'suggested_tools': ['web_search', 'text_generation'],
    'system_messages': ['조사하세요.', '작성하세요.'],
    'confidence_score': 0.88,
    'model_used': 'mock',
}


class TransformApiTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email='author@example.com', username='author', password='StrongPass123!',
        )
        self.other = User.objects.create_user(
            email='other@example.com', username='other', password='StrongPass123!',
        )
        self.category = Category.objects.create(name='개발', slug='dev')
        self.prompt = Prompt.objects.create(
            user=self.author,
            category=self.category,
            title='변환 대상 프롬프트',
            content='서울 여행 일정을 짜는 프롬프트 본문입니다.',
            ai_model='gpt-5-5',
            prompt_type='single_prompt',
        )

    @patch('ai_gateway.views.transform_prompt.delay')
    def test_author_can_enqueue_transform(self, mock_delay):
        self.client.force_authenticate(user=self.author)

        response = self.client.post(f'/api/prompts/{self.prompt.id}/transform/')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.data)
        self.assertIn('task_id', response.data)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertIn('/api/tasks/', response.data['status_url'])
        self.assertTrue(Task.objects.filter(prompt=self.prompt, task_type='transform').exists())
        mock_delay.assert_called_once()

    def test_non_author_cannot_transform(self):
        self.client.force_authenticate(user=self.other)

        response = self.client.post(f'/api/prompts/{self.prompt.id}/transform/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Task.objects.filter(prompt=self.prompt).count(), 0)

    def test_anonymous_cannot_transform(self):
        response = self.client.post(f'/api/prompts/{self.prompt.id}/transform/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agent_recipe_cannot_transform(self):
        self.prompt.prompt_type = 'agent_recipe'
        self.prompt.save(update_fields=['prompt_type'])
        self.client.force_authenticate(user=self.author)

        response = self.client.post(f'/api/prompts/{self.prompt.id}/transform/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('단일 프롬프트', response.data['detail'])


class AgentDetailApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='reader@example.com', username='reader', password='StrongPass123!',
        )
        self.category = Category.objects.create(name='개발', slug='dev')
        self.prompt = Prompt.objects.create(
            user=self.user,
            category=self.category,
            title='에이전트 결과 테스트',
            content='본문',
            ai_model='gpt-5-5',
        )
        self.transformation = AgentTransformation.objects.create(
            prompt=self.prompt,
            decomposed_steps=MOCK_TRANSFORM['decomposed_steps'],
            suggested_tools=MOCK_TRANSFORM['suggested_tools'],
            system_messages=MOCK_TRANSFORM['system_messages'],
            confidence_score=0.88,
            model_used='mock',
        )

    def test_agent_detail_returns_latest_transformation(self):
        response = self.client.get(f'/api/prompts/{self.prompt.id}/agent/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['decomposed_steps']), 2)
        self.assertEqual(response.data['model_used'], 'mock')
        self.assertAlmostEqual(response.data['confidence_score'], 0.88)

    def test_agent_detail_404_when_missing(self):
        empty_prompt = Prompt.objects.create(
            user=self.user,
            category=self.category,
            title='결과 없음',
            content='본문',
            ai_model='gpt-5-5',
        )
        response = self.client.get(f'/api/prompts/{empty_prompt.id}/agent/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TaskStatusApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='task@example.com', username='taskuser', password='StrongPass123!',
        )
        self.category = Category.objects.create(name='개발', slug='dev')
        self.prompt = Prompt.objects.create(
            user=self.user,
            category=self.category,
            title='태스크 테스트',
            content='본문',
            ai_model='gpt-5-5',
        )
        self.task = Task.objects.create(
            task_id=uuid.uuid4(),
            task_type='transform',
            status='SUCCESS',
            prompt=self.prompt,
            user=self.user,
            result_id=1,
        )

    def test_owner_can_poll_task_status(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f'/api/tasks/{self.task.task_id}/status/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'SUCCESS')
        self.assertIn('/api/prompts/', response.data['result_url'])

    def test_other_user_cannot_read_task(self):
        other = User.objects.create_user(
            email='other2@example.com', username='other2', password='StrongPass123!',
        )
        self.client.force_authenticate(user=other)

        response = self.client.get(f'/api/tasks/{self.task.task_id}/status/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SimilarPromptsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='sim@example.com', username='simuser', password='StrongPass123!',
        )
        self.category = Category.objects.create(name='개발', slug='dev')
        self.base = Prompt.objects.create(
            user=self.user, category=self.category,
            title='기준 프롬프트', content='본문 A', ai_model='gpt-5-5',
        )
        self.similar = Prompt.objects.create(
            user=self.user, category=self.category,
            title='유사 프롬프트', content='본문 B', ai_model='gpt-5-5',
        )
        self.different = Prompt.objects.create(
            user=self.user, category=self.category,
            title='다른 프롬프트', content='본문 C', ai_model='gpt-5-5',
        )
        PromptEmbedding.objects.create(prompt=self.base, vector=[1.0, 0.0, 0.0])
        PromptEmbedding.objects.create(prompt=self.similar, vector=[0.9, 0.1, 0.0])
        PromptEmbedding.objects.create(prompt=self.different, vector=[0.0, 0.0, 1.0])

    def test_similar_returns_ranked_prompts(self):
        response = self.client.get(f'/api/prompts/{self.base.id}/similar/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.similar.id)
        self.assertGreater(response.data[0]['similarity'], 0.5)

    def test_similar_empty_without_embedding(self):
        bare = Prompt.objects.create(
            user=self.user, category=self.category,
            title='임베딩 없음', content='본문', ai_model='gpt-5-5',
        )
        response = self.client.get(f'/api/prompts/{bare.id}/similar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class MyTransformationsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='mine@example.com', username='mine', password='StrongPass123!',
        )
        self.category = Category.objects.create(name='개발', slug='dev')
        self.prompt = Prompt.objects.create(
            user=self.user,
            category=self.category,
            title='내 변환 프롬프트',
            content='본문',
            ai_model='gpt-5-5',
        )
        self.transformation = AgentTransformation.objects.create(
            prompt=self.prompt,
            decomposed_steps=MOCK_TRANSFORM['decomposed_steps'],
            suggested_tools=[],
            system_messages=[],
            confidence_score=0.9,
            model_used='mock',
        )
        Task.objects.create(
            task_id=uuid.uuid4(),
            task_type='transform',
            status='SUCCESS',
            prompt=self.prompt,
            user=self.user,
            result_id=self.transformation.id,
        )

    def test_me_transformations_lists_owned_latest(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/accounts/me/transformations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['prompt_id'], self.prompt.id)
        self.assertEqual(response.data[0]['transformation_id'], self.transformation.id)
        self.assertIsNotNone(response.data[0]['task_id'])


class BlueprintDesignApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='design@example.com', username='designer', password='StrongPass123!',
        )
        self.category = Category.objects.create(name='개발', slug='dev')
        self.prompt = Prompt.objects.create(
            user=self.user,
            category=self.category,
            title='[설계 초안] 테스트',
            content='자동화 요청 본문입니다.',
            ai_model='other',
            is_blueprint_draft=True,
        )
        self.transformation = AgentTransformation.objects.create(
            prompt=self.prompt,
            decomposed_steps=MOCK_TRANSFORM['decomposed_steps'],
            suggested_tools=MOCK_TRANSFORM['suggested_tools'],
            system_messages=MOCK_TRANSFORM['system_messages'],
            confidence_score=0.88,
            model_used='mock',
            overall_pattern='Sequential',
        )
        self.design = BlueprintDesign.objects.create(
            user=self.user,
            title='테스트 설계',
            brief='주간 리포트 자동화가 필요합니다.',
            status='success',
            source_prompt=self.prompt,
            transformation=self.transformation,
        )

    @patch('ai_gateway.blueprint_views.transform_prompt.delay')
    def test_create_blueprint_design(self, mock_delay):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/blueprints/design/', {
            'brief': '매일 슬랙에 요약을 보내는 자동화를 만들고 싶습니다.',
            'extra_context': 'GA4 사용 중',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.data)
        self.assertIn('id', response.data)
        self.assertIn('task_id', response.data)
        self.assertTrue(BlueprintDesign.objects.filter(user=self.user).exists())
        mock_delay.assert_called_once()

    def test_anonymous_cannot_create_design(self):
        response = self.client.post('/api/blueprints/design/', {
            'brief': '로그인 없이는 안 됩니다.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_own_design_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/blueprints/design/{self.design.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], '테스트 설계')
        self.assertEqual(len(response.data['transformation']['decomposed_steps']), 2)

    def test_design_syncs_when_task_done_but_status_stale(self):
        self.design.status = 'processing'
        self.design.transformation = None
        self.design.save(update_fields=['status', 'transformation'])
        Task.objects.create(
            task_id=uuid.uuid4(),
            task_type='blueprint_design',
            status='SUCCESS',
            prompt=self.prompt,
            user=self.user,
            result_id=self.transformation.id,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/blueprints/design/{self.design.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['transformation']['id'], self.transformation.id)

    def test_publish_recipe_from_design(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/api/blueprints/design/{self.design.id}/publish-recipe/',
            {'recipe_category_name': '마케팅'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        recipe = Prompt.objects.get(pk=response.data['recipe_id'])
        self.assertEqual(recipe.prompt_type, 'agent_recipe')
        self.assertEqual(recipe.agent_pattern, 'sequential')
        self.assertEqual(len(recipe.workflow_steps), 2)
        self.design.refresh_from_db()
        self.assertEqual(self.design.recipe_id, recipe.id)
