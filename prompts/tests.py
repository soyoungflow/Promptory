from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, RecipeCategory, Prompt, Tag


User = get_user_model()


class PromptApiContractTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='StrongPass123!',
        )
        self.other = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='StrongPass123!',
        )
        self.category = Category.objects.create(name='개발', slug='dev')
        self.tag = Tag.objects.create(name='Python', slug='python')

    def test_prompt_create_accepts_existing_and_new_tags(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.post('/api/prompts/', {
            'title': '테스트 프롬프트',
            'content': '테스트 본문',
            'description': '설명',
            'ai_model': 'gpt-5-5',
            'category': self.category.id,
            'tag_ids': [self.tag.id],
            'tag_names': ['Django'],
            'is_free': True,
            'price': '0.00',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

        prompt = Prompt.objects.get(id=response.data['id'])
        self.assertEqual(prompt.tags.count(), 2)
        self.assertTrue(prompt.tags.filter(name='Django').exists())

    def test_prompt_detail_exposes_frontend_contract_fields(self):
        prompt = Prompt.objects.create(
            user=self.author,
            category=self.category,
            title='상세 프롬프트',
            content='본문',
            ai_model='gpt-5-5',
        )
        prompt.tags.add(self.tag)
        self.client.force_authenticate(user=self.other)

        response = self.client.get(f'/api/prompts/{prompt.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.author.id)
        self.assertIn('is_liked', response.data)
        self.assertIn('is_bookmarked', response.data)
        self.assertEqual(response.data['tags'][0]['name'], 'Python')

    def test_non_author_cannot_update_prompt(self):
        prompt = Prompt.objects.create(
            user=self.author,
            title='원본',
            content='본문',
            ai_model='gpt-5-5',
        )
        self.client.force_authenticate(user=self.other)

        response = self.client.put(f'/api/prompts/{prompt.id}/', {
            'title': '수정',
            'content': '수정 본문',
            'ai_model': 'gpt-5-5',
            'is_free': True,
            'price': '0.00',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_prompt_file_upload_accepts_zip_under_10mb(self):
        prompt = Prompt.objects.create(
            user=self.author,
            title='파일 프롬프트',
            content='본문',
            ai_model='gpt-5-5',
        )
        self.client.force_authenticate(user=self.author)
        upload = SimpleUploadedFile(
            'template.zip',
            b'zip-content',
            content_type='application/zip',
        )

        response = self.client.post(
            f'/api/prompts/{prompt.id}/files/',
            {'file': upload},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['file_name'], 'template.zip')

    def test_prompt_create_requires_category(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.post('/api/prompts/', {
            'title': '카테고리 없는 프롬프트',
            'content': '본문',
            'ai_model': 'gpt-5-5',
            'is_free': True,
            'price': '0.00',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

    def test_agent_recipe_create_uses_recipe_category_not_ai_model(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.post('/api/prompts/', {
            'title': '마케팅 에이전트 레시피',
            'content': '시스템 프롬프트 본문입니다.',
            'description': '설명',
            'prompt_type': 'agent_recipe',
            'agent_pattern': 'sequential',
            'recipe_category_name': '마케팅',
            'workflow_steps': [{
                'name': '리서치',
                'system_message': '주제를 조사하세요.',
                'tool': 'web_search',
            }],
            'is_free': True,
            'price': '0.00',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        prompt = Prompt.objects.get(id=response.data['id'])
        self.assertEqual(prompt.prompt_type, 'agent_recipe')
        self.assertEqual(prompt.ai_model, 'other')
        self.assertIsNone(prompt.category_id)
        self.assertEqual(prompt.recipe_category.name, '마케팅')
        self.assertTrue(RecipeCategory.objects.filter(name='마케팅').exists())
