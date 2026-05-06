from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AccountApiTests(APITestCase):
    def test_register_returns_jwt_and_user_contract(self):
        response = self.client.post('/api/accounts/register/', {
            'email': 'user@example.com',
            'username': 'tester',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'user@example.com')

    def test_me_requires_jwt(self):
        user = User.objects.create_user(
            email='me@example.com',
            username='me',
            password='StrongPass123!',
        )
        self.client.force_authenticate(user=user)

        response = self.client.get('/api/accounts/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'me@example.com')

    def test_my_prompts_returns_only_own_prompts(self):
        from prompts.models import Prompt

        u1 = User.objects.create_user(
            email='author1@example.com',
            username='a1',
            password='StrongPass123!',
        )
        u2 = User.objects.create_user(
            email='author2@example.com',
            username='a2',
            password='StrongPass123!',
        )
        p1 = Prompt.objects.create(user=u1, title='Mine', content='body')
        p2 = Prompt.objects.create(user=u2, title='Other', content='body')
        self.client.force_authenticate(user=u1)
        response = self.client.get('/api/accounts/me/prompts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data]
        self.assertIn(p1.id, ids)
        self.assertNotIn(p2.id, ids)

    def test_my_prompts_requires_auth(self):
        response = self.client.get('/api/accounts/me/prompts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JwtOnlyTemplateTests(TestCase):
    def test_protected_form_pages_render_without_django_session(self):
        response = self.client.get('/prompts/new/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="prompt-form"')

    def test_library_page_renders(self):
        response = self.client.get('/library/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="library-main"')
