import json
import os

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from mock import mock_embed, mock_transform
from schemas import EmbedRequest, EmbedResponse, HealthResponse, TransformRequest, TransformResponse

app = FastAPI(title='Promptory AI Server')
Instrumentator().instrument(app).expose(app)

PROVIDER = os.getenv('LLM_PROVIDER', 'mock')


@app.get('/health', response_model=HealthResponse)
def health():
    if PROVIDER == 'mock':
        return HealthResponse(status='ok', model_loaded=True, provider='mock')
    try:
        from models.llm import get_model  # noqa: WPS433

        get_model()
        return HealthResponse(status='ok', model_loaded=True, provider='huggingface')
    except Exception:
        return HealthResponse(status='loading', model_loaded=False, provider='huggingface')


@app.post('/transform', response_model=TransformResponse)
def transform(req: TransformRequest):
    if PROVIDER == 'mock':
        return mock_transform(req.prompt_text)

    from models.llm import generate  # noqa: WPS433

    system = (
        f'다음 사용자 프롬프트를 {req.max_steps}단계 에이전트 워크플로우로 분해해. '
        '반드시 JSON만 응답: {"steps":[{"step":1,"name":"...","system_message":"...","tool":"..."}],'
        '"tools":["..."],"confidence":0.0-1.0}\n\n'
        f'사용자 프롬프트: {req.prompt_text}'
    )
    text = generate(system, max_new_tokens=512)
    try:
        data = json.loads(text)
        steps = [
            {
                'step': s['step'],
                'name': s['name'],
                'system_message': s['system_message'],
                'tool': s.get('tool', ''),
            }
            for s in data['steps']
        ]
        return TransformResponse(
            decomposed_steps=steps,
            suggested_tools=data.get('tools', []),
            system_messages=[s['system_message'] for s in steps],
            confidence_score=float(data.get('confidence', 0.7)),
            model_used=os.getenv('HF_MODEL_NAME', 'exaone'),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=500, detail=f'LLM parse error: {exc}') from exc


@app.post('/embed', response_model=EmbedResponse)
def embed(req: EmbedRequest):
    if PROVIDER == 'mock':
        return mock_embed(req.text)

    from models.embedding import embed as do_embed  # noqa: WPS433

    vector = do_embed(req.text)
    return EmbedResponse(
        vector=vector,
        dim=len(vector),
        model_name=os.getenv('HF_EMBEDDING_MODEL', 'jhgan/ko-sroberta-multitask'),
    )
