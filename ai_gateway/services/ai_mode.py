from django.conf import settings


def get_ai_mode() -> str:
    """Return normalized AI mode: 'mock' | 'real'."""
    mode = getattr(settings, 'AI_MODE', 'mock')
    return 'real' if mode == 'real' else 'mock'


def resolve_ai_mode(raw: str | None = None) -> str:
    """Map env values (incl. legacy LLM_PROVIDER) to mock|real."""
    value = (raw or 'mock').strip().lower()
    if value in ('real', 'huggingface', 'hf'):
        return 'real'
    return 'mock'
