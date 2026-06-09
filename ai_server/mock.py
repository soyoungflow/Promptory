import hashlib
import struct

from schemas import (
    ContextPolicy,
    EmbedResponse,
    HarnessPolicy,
    StepSpec,
    TransformResponse,
)

MOCK_STEPS = [
    StepSpec(
        step=1, name='리서치',
        system_message='주제 관련 최신 정보 5개 수집',
        tool='web_search',
        context_policy=ContextPolicy(
            previous_output_strategy='none',
            memory_scope='this_step_only',
            reason='첫 단계는 사용자 원본 프롬프트만 입력',
        ),
        harness_policy=HarnessPolicy(
            timeout_seconds=45,
            max_retries=3,
            fallback_action='use_default',
            cost_budget_tokens=3000,
            rate_limit='5/min',
        ),
    ),
    StepSpec(
        step=2, name='개요',
        system_message='H2/H3 헤딩으로 구조화',
        tool='outline_generator',
        context_policy=ContextPolicy(
            previous_output_strategy='summarize_500',
            memory_scope='all_previous',
            reason='리서치 결과 5000자가 누적되면 컨텍스트 폭발 — 요약 필수',
        ),
        harness_policy=HarnessPolicy(
            timeout_seconds=20,
            max_retries=2,
            validation_schema='outline_v1.json',
            cost_budget_tokens=1500,
        ),
    ),
    StepSpec(
        step=3, name='초안',
        system_message='개요 각 섹션을 300자 이상 풀어쓰기',
        tool='text_generation',
        context_policy=ContextPolicy(
            previous_output_strategy='full',
            memory_scope='all_previous',
            reason='개요는 짧고 초안 생성에 필수',
        ),
        harness_policy=HarnessPolicy(
            timeout_seconds=60,
            max_retries=2,
            cost_budget_tokens=4000,
        ),
    ),
    StepSpec(
        step=4, name='검토',
        system_message='문법/사실관계/일관성 검토',
        tool='reflection',
        context_policy=ContextPolicy(
            previous_output_strategy='selective',
            memory_scope='all_previous',
            reason='초안만 입력, 리서치 원본은 사실 검증용으로만 query',
        ),
        harness_policy=HarnessPolicy(
            timeout_seconds=30,
            max_retries=1,
            fallback_action='skip_step',
            cost_budget_tokens=2000,
        ),
    ),
]


def mock_transform(prompt_text: str) -> TransformResponse:
    return TransformResponse(
        decomposed_steps=MOCK_STEPS,
        suggested_tools=['web_search', 'outline_generator', 'text_generation', 'reflection'],
        system_messages=[s.system_message for s in MOCK_STEPS],
        confidence_score=0.92,
        model_used='mock',
        overall_pattern='Sequential',
        context_strategy_summary='리서치 결과는 요약, 개요는 전체 전달, 검토는 선택적',
        harness_strategy_summary='리서치 단계만 긴 타임아웃 + 재시도 3회, 나머지는 표준',
    )


def mock_embed(text: str) -> EmbedResponse:
    seed = hashlib.sha256(text.encode()).digest()
    vector = []
    for i in range(0, min(len(seed) * 4, 768), 4):
        chunk = (seed[i % len(seed): i % len(seed) + 4] or seed[:4])
        chunk = (chunk * 4)[:4]
        vector.append(struct.unpack('f', chunk)[0] % 1.0)
    while len(vector) < 768:
        vector.extend(vector[: max(0, 768 - len(vector))])
    vector = vector[:768]
    return EmbedResponse(vector=vector, dim=768, model_name='mock')
