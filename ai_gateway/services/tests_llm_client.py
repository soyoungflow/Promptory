from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from ai_gateway.services.llm_client import LLMClient


@override_settings(AI_MODE='mock', FASTAPI_URL='http://ai_server:8000')
class LLMClientMockModeTests(TestCase):
    def test_transform_returns_mock_without_http(self):
        with patch('ai_gateway.services.llm_client.httpx.Client') as mock_client:
            result = LLMClient().transform('테스트 프롬프트 본문입니다.')
            mock_client.assert_not_called()
        self.assertEqual(result['ai_mode'], 'mock')
        self.assertEqual(result['model_used'], 'mock')
        self.assertEqual(len(result['decomposed_steps']), 4)


@override_settings(AI_MODE='real', FASTAPI_URL='http://ai_server:8000')
class LLMClientRealModeTests(TestCase):
    def test_transform_calls_fastapi(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'decomposed_steps': [{'step': 1, 'name': 'A', 'system_message': 'x', 'tool': 't'}],
            'suggested_tools': [],
            'system_messages': ['x'],
            'confidence_score': 0.5,
            'model_used': 'Qwen/Qwen2.5-1.5B-Instruct',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('ai_gateway.services.llm_client.httpx.Client') as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = LLMClient().transform('테스트 프롬프트 본문입니다.')

        mock_client.post.assert_called_once()
        self.assertEqual(result['ai_mode'], 'real')
        self.assertEqual(result['model_used'], 'Qwen/Qwen2.5-1.5B-Instruct')
