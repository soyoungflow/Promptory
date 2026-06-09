import json
import os
import re

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from mock import mock_embed, mock_transform
from schemas import (
    ContextPolicy,
    EmbedRequest,
    EmbedResponse,
    HarnessPolicy,
    HealthResponse,
    StepSpec,
    TransformRequest,
    TransformResponse,
)

app = FastAPI(title='Promptory AI Server')
Instrumentator().instrument(app).expose(app)

PROVIDER = os.getenv('LLM_PROVIDER', 'mock')

HF_TRANSFORM_SYSTEM = """다음 사용자 프롬프트를 {max_steps}단계 에이전트 워크플로우로 분해해.
각 단계마다 다음 3가지를 결정해:

1. Agent Design: 무엇을 할지 (name, system_message, tool)
2. Context Policy: 이전 단계 출력을 어떻게 전달할지
   - previous_output_strategy: "full" | "summarize_500" | "selective" | "vector_query" | "none"
   - memory_scope: "this_step_only" | "all_previous" | "user_session"
   - reason: 왜 이 정책인지 한 문장
3. Harness Policy: 실행 안전 정책
   - timeout_seconds: 5-300
   - max_retries: 0-5
   - fallback_action: "skip_step" | "use_default" | "fail_fast"
   - cost_budget_tokens: 100-20000

반드시 다음 JSON으로만 응답:
{{
  "steps": [
    {{
      "step": 1,
      "name": "...",
      "system_message": "...",
      "tool": "...",
      "context_policy": {{
        "previous_output_strategy": "...",
        "memory_scope": "...",
        "reason": "..."
      }},
      "harness_policy": {{
        "timeout_seconds": 30,
        "max_retries": 2,
        "fallback_action": "...",
        "cost_budget_tokens": 2000
      }}
    }}
  ],
  "tools": ["..."],
  "confidence": 0.0-1.0,
  "overall_pattern": "Sequential|ReAct|Reflection|MultiAgent",
  "context_strategy_summary": "전체 한 줄 요약",
  "harness_strategy_summary": "전체 한 줄 요약"
}}

사용자 프롬프트: {prompt_text}"""


def _extract_json_object(text: str) -> dict:
    """LLM 출력에서 JSON 객체를 추출한다 (마크다운 펜스·잡텍스트 허용)."""
    raw = (text or '').strip()
    if not raw:
        raise ValueError('empty LLM response')

    candidates = [raw]
    for block in re.findall(r'```(?:json)?\s*([\s\S]*?)```', raw, flags=re.IGNORECASE):
        candidates.append(block.strip())

    start = raw.find('{')
    end = raw.rfind('}')
    if start >= 0 and end > start:
        candidates.append(raw[start:end + 1])

    last_error = None
    for candidate in candidates:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
    raise ValueError(f'JSON parse failed: {last_error}')


def _normalize_policy(raw: dict | None, model_cls):
    if not isinstance(raw, dict):
        return model_cls()
    try:
        return model_cls(**raw)
    except Exception:
        return model_cls()


def _normalize_steps(data: dict) -> list[StepSpec]:
    steps_raw = data.get('steps') or data.get('decomposed_steps') or []
    if not isinstance(steps_raw, list):
        return []
    steps = []
    for item in steps_raw:
        if not isinstance(item, dict):
            continue
        steps.append(StepSpec(
            step=int(item.get('step', len(steps) + 1)),
            name=str(item.get('name', '') or f'Step {len(steps) + 1}'),
            system_message=str(item.get('system_message', '') or ''),
            tool=str(item.get('tool', '') or ''),
            context_policy=_normalize_policy(item.get('context_policy'), ContextPolicy),
            harness_policy=_normalize_policy(item.get('harness_policy'), HarnessPolicy),
        ))
    return steps


def _build_transform_response(data: dict, steps: list[StepSpec]) -> TransformResponse:
    tools = data.get('tools') or data.get('suggested_tools') or []
    if not isinstance(tools, list):
        tools = []
    pattern = data.get('overall_pattern', 'Sequential')
    if pattern not in ('Sequential', 'ReAct', 'Reflection', 'MultiAgent'):
        pattern = 'Sequential'
    return TransformResponse(
        decomposed_steps=steps,
        suggested_tools=[str(t) for t in tools],
        system_messages=[s.system_message for s in steps],
        confidence_score=float(data.get('confidence', data.get('confidence_score', 0.7))),
        model_used=os.getenv('HF_MODEL_NAME', 'exaone'),
        overall_pattern=pattern,
        context_strategy_summary=str(data.get('context_strategy_summary', '') or ''),
        harness_strategy_summary=str(data.get('harness_strategy_summary', '') or ''),
    )


@app.get('/health', response_model=HealthResponse)
def health():
    if PROVIDER == 'mock':
        return HealthResponse(status='ok', model_loaded=True, provider='mock')
    from models.llm import is_model_loaded  # noqa: WPS433

    loaded = is_model_loaded()
    return HealthResponse(
        status='ok' if loaded else 'loading',
        model_loaded=loaded,
        provider='huggingface',
    )


@app.post('/transform', response_model=TransformResponse)
def transform(req: TransformRequest):
    if PROVIDER == 'mock':
        return mock_transform(req.prompt_text)

    from models.llm import generate  # noqa: WPS433

    system = HF_TRANSFORM_SYSTEM.format(
        max_steps=req.max_steps,
        prompt_text=req.prompt_text,
    )
    text = generate(system, max_new_tokens=768)
    try:
        data = _extract_json_object(text)
        steps = _normalize_steps(data)
        if not steps:
            raise ValueError('no workflow steps in LLM JSON')
        return _build_transform_response(data, steps)
    except (ValueError, KeyError, TypeError) as exc:
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
