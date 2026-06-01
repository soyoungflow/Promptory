import numpy as np

from ai_gateway.models import PromptEmbedding
from prompts.models import Prompt


def cosine_similarity(a: list, b: list) -> float:
    av, bv = np.array(a, dtype=float), np.array(b, dtype=float)
    denom = np.linalg.norm(av) * np.linalg.norm(bv)
    if denom < 1e-9:
        return 0.0
    return float(np.dot(av, bv) / denom)


def find_similar(prompt_id: int, top_k: int = 5) -> list[dict]:
    try:
        target = PromptEmbedding.objects.select_related('prompt').get(prompt_id=prompt_id)
    except PromptEmbedding.DoesNotExist:
        return []

    others = PromptEmbedding.objects.exclude(prompt_id=prompt_id).filter(
        prompt__is_deleted=False,
    ).select_related('prompt')

    scored = []
    for item in others:
        scored.append({
            'id': item.prompt_id,
            'title': item.prompt.title,
            'similarity': round(cosine_similarity(target.vector, item.vector), 4),
        })
    scored.sort(key=lambda row: -row['similarity'])
    return scored[:top_k]
