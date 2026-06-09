import httpx
from django.conf import settings


class LLMClient:
    def __init__(self):
        self.base_url = settings.FASTAPI_URL.rstrip('/')
        self.timeout = httpx.Timeout(300.0, connect=10.0)

    def transform(self, prompt_text: str, max_steps: int = 4) -> dict:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f'{self.base_url}/transform',
                json={'prompt_text': prompt_text, 'max_steps': max_steps},
            )
            response.raise_for_status()
            return response.json()

    def embed(self, text: str) -> dict:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f'{self.base_url}/embed', json={'text': text})
            response.raise_for_status()
            return response.json()

    def health(self) -> dict:
        with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
            response = client.get(f'{self.base_url}/health')
            response.raise_for_status()
            return response.json()
