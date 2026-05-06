from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from prompts.models import Prompt
from .models import Bookmark, Comment, Like


User = get_user_model()


class InteractionApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='StrongPass123!',
        )
        self.prompt = Prompt.objects.create(
            user=self.user,
            title='프롬프트',
            content='본문',
            ai_model='gpt-5-5',
        )

    def test_comment_response_includes_user_id_for_frontend_permissions(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(f'/api/prompts/{self.prompt.id}/comments/', {
            'content': '댓글입니다.',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertEqual(response.data['author'], self.user.email)

    def test_like_toggle_creates_and_removes_like(self):
        self.client.force_authenticate(user=self.user)

        first = self.client.post(f'/api/prompts/{self.prompt.id}/like/')
        second = self.client.post(f'/api/prompts/{self.prompt.id}/like/')

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertTrue(first.data['liked'])
        self.assertFalse(second.data['liked'])
        self.assertFalse(Like.objects.filter(prompt=self.prompt, user=self.user).exists())

    def test_bookmark_toggle_creates_and_removes_bookmark(self):
        self.client.force_authenticate(user=self.user)

        first = self.client.post(f'/api/prompts/{self.prompt.id}/bookmark/')
        second = self.client.post(f'/api/prompts/{self.prompt.id}/bookmark/')

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertTrue(first.data['bookmarked'])
        self.assertFalse(second.data['bookmarked'])
        self.assertFalse(Bookmark.objects.filter(prompt=self.prompt, user=self.user).exists())

    def test_comment_soft_delete_hides_comment_from_list(self):
        comment = Comment.objects.create(
            prompt=self.prompt,
            user=self.user,
            content='삭제될 댓글',
        )
        self.client.force_authenticate(user=self.user)

        delete_response = self.client.delete(f'/api/comments/{comment.id}/')
        list_response = self.client.get(f'/api/prompts/{self.prompt.id}/comments/')

        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data, [])

    def test_my_likes_lists_liked_prompts(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f'/api/prompts/{self.prompt.id}/like/')
        response = self.client.get('/api/accounts/me/likes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data]
        self.assertIn(self.prompt.id, ids)

    def test_my_likes_requires_auth(self):
        response = self.client.get('/api/accounts/me/likes/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_my_comments_lists_with_prompt_context(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            f'/api/prompts/{self.prompt.id}/comments/',
            {'content': '보관함 테스트 댓글'},
            format='json',
        )
        response = self.client.get('/api/accounts/me/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['prompt_id'], self.prompt.id)
        self.assertEqual(response.data[0]['prompt_title'], self.prompt.title)

    def test_my_comments_excludes_soft_deleted(self):
        comment = Comment.objects.create(
            prompt=self.prompt,
            user=self.user,
            content='숨김됨',
        )
        comment.soft_delete()
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/accounts/me/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
