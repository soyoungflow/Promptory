import httpx
import structlog
from django.conf import settings

from .ai_mode import get_ai_mode
from .mock_transform import mock_embed_result, mock_transform_result

logger = structlog.get_logger()


class LLMClient:
    def __init__(self):
        self.base_url = settings.FASTAPI_URL.rstrip('/')
        self.timeout = httpx.Timeout(300.0, connect=10.0)

    def transform(self, prompt_text: str, max_steps: int = 4) -> dict:
        mode = get_ai_mode()
        if mode == 'mock':
            result = mock_transform_result()
            logger.info('ai_transform_mock', ai_mode='mock', max_steps=max_steps)
            return result

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f'{self.base_url}/transform',
                json={'prompt_text': prompt_text, 'max_steps': max_steps},
            )
            response.raise_for_status()
            result = response.json()
        result['ai_mode'] = 'real'
        logger.info(
            'ai_transform_real',
            ai_mode='real',
            model_used=result.get('model_used'),
            fastapi_url=self.base_url,
        )
        return result

    def embed(self, text: str) -> dict:
        mode = get_ai_mode()
        if mode == 'mock':
            result = mock_embed_result(text)
            logger.info('ai_embed_mock', ai_mode='mock')
            return result

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f'{self.base_url}/embed', json={'text': text})
            response.raise_for_status()
            result = response.json()
        result['ai_mode'] = 'real'
        logger.info(
            'ai_embed_real',
            ai_mode='real',
            model_name=result.get('model_name'),
            fastapi_url=self.base_url,
        )
        return result

    def health(self) -> dict:
        with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
            response = client.get(f'{self.base_url}/health')
            response.raise_for_status()
            return response.json()
