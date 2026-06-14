import httpx
import structlog
from django.conf import settings

from .ai_mode import get_ai_mode

logger = structlog.get_logger()


class LLMClient:
    """Django/Celery → FastAPI ai_server (/transform, /embed) 단일 진입.

    mock/real 분기는 ai_server 가 LLM_PROVIDER(AI_MODE) 로 처리한다.
    """

    def __init__(self):
        self.base_url = settings.FASTAPI_URL.rstrip('/')
        self.timeout = httpx.Timeout(300.0, connect=10.0)

    def _annotate_mode(self, result: dict) -> dict:
        model_key = (result.get('model_used') or result.get('model_name') or '').lower()
        result['ai_mode'] = 'mock' if model_key == 'mock' else get_ai_mode()
        return result

    def transform(self, prompt_text: str, max_steps: int = 4) -> dict:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f'{self.base_url}/transform',
                json={'prompt_text': prompt_text, 'max_steps': max_steps},
            )
            response.raise_for_status()
            result = self._annotate_mode(response.json())
        logger.info(
            'ai_transform',
            ai_mode=result.get('ai_mode'),
            model_used=result.get('model_used'),
            fastapi_url=self.base_url,
            max_steps=max_steps,
        )
        return result

    def embed(self, text: str) -> dict:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f'{self.base_url}/embed', json={'text': text})
            response.raise_for_status()
            result = self._annotate_mode(response.json())
        logger.info(
            'ai_embed',
            ai_mode=result.get('ai_mode'),
            model_name=result.get('model_name'),
            fastapi_url=self.base_url,
        )
        return result

    def health(self) -> dict:
        with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
            response = client.get(f'{self.base_url}/health')
            response.raise_for_status()
            return response.json()
