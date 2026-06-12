"""고정 mock 변환·임베딩 결과 — AI_MODE=mock 일 때 Django/Celery에서만 사용."""

import hashlib
import struct


def mock_transform_result() -> dict:
    """ai_server/mock.py 와 동일한 4단계 고정 JSON (dict)."""
    steps = [
        {
            'step': 1,
            'name': '리서치',
            'system_message': '주제 관련 최신 정보 5개 수집',
            'tool': 'web_search',
            'context_policy': {
                'previous_output_strategy': 'none',
                'memory_scope': 'this_step_only',
                'reason': '첫 단계는 사용자 원본 프롬프트만 입력',
            },
            'harness_policy': {
                'timeout_seconds': 45,
                'max_retries': 3,
                'fallback_action': 'use_default',
                'cost_budget_tokens': 3000,
                'rate_limit': '5/min',
            },
            'knowledge_refs': [
                {
                    'type': 'api',
                    'source': '네이버 블로그 검색 API',
                    'usage': 'always',
                    'description': '국내 최신 트렌드 확보',
                },
            ],
            'verification_criteria': {
                'success_signals': ['URL 5개 이상 수집'],
                'failure_signals': ['검색 결과 0건'],
                'evaluator': 'rule',
                'min_quality_score': 0.7,
                'on_fail': 'retry',
            },
        },
        {
            'step': 2,
            'name': '개요',
            'system_message': 'H2/H3 헤딩으로 구조화',
            'tool': 'outline_generator',
            'context_policy': {
                'previous_output_strategy': 'summarize_500',
                'memory_scope': 'all_previous',
                'reason': '리서치 결과 요약 전달',
            },
            'harness_policy': {
                'timeout_seconds': 20,
                'max_retries': 2,
                'fallback_action': 'fail_fast',
                'cost_budget_tokens': 1500,
            },
            'knowledge_refs': [],
            'verification_criteria': {
                'evaluator': 'rule',
                'min_quality_score': 0.75,
                'on_fail': 'retry',
            },
        },
        {
            'step': 3,
            'name': '초안',
            'system_message': '개요 각 섹션을 300자 이상 풀어쓰기',
            'tool': 'text_generation',
            'context_policy': {
                'previous_output_strategy': 'full',
                'memory_scope': 'all_previous',
                'reason': '개요 전체를 초안 작성에 활용',
            },
            'harness_policy': {
                'timeout_seconds': 60,
                'max_retries': 1,
                'fallback_action': 'skip_step',
                'cost_budget_tokens': 4000,
            },
            'knowledge_refs': [],
            'verification_criteria': {
                'evaluator': 'llm_judge',
                'min_quality_score': 0.7,
                'on_fail': 'retry',
            },
        },
        {
            'step': 4,
            'name': '검토',
            'system_message': '문법·톤·사실관계 점검 후 수정 제안',
            'tool': 'reflection',
            'context_policy': {
                'previous_output_strategy': 'selective',
                'memory_scope': 'this_step_only',
                'reason': '초안만 검토 대상',
            },
            'harness_policy': {
                'timeout_seconds': 30,
                'max_retries': 0,
                'fallback_action': 'escalate',
                'cost_budget_tokens': 2000,
            },
            'knowledge_refs': [],
            'verification_criteria': {
                'evaluator': 'llm_judge',
                'min_quality_score': 0.8,
                'on_fail': 'escalate',
            },
        },
    ]
    return {
        'decomposed_steps': steps,
        'suggested_tools': ['web_search', 'outline_generator', 'text_generation', 'reflection'],
        'system_messages': [s['system_message'] for s in steps],
        'confidence_score': 0.92,
        'model_used': 'mock',
        'overall_pattern': 'Sequential',
        'context_strategy_summary': '리서치 결과는 요약, 개요는 전체 전달, 검토는 선택적',
        'harness_strategy_summary': '리서치 단계만 긴 타임아웃 + 재시도 3회, 나머지는 표준',
        'quality_strategy_summary': '리서치는 규칙 검증, 초안/검토는 LLM judge로 품질 보장',
        'ai_mode': 'mock',
    }


def mock_embed_result(text: str) -> dict:
    seed = hashlib.sha256(text.encode()).digest()
    vector = []
    for i in range(0, min(len(seed) * 4, 768), 4):
        chunk = (seed[i % len(seed): i % len(seed) + 4] or seed[:4])
        chunk = (chunk * 4)[:4]
        vector.append(struct.unpack('f', chunk)[0] % 1.0)
    while len(vector) < 768:
        vector.extend(vector[: max(0, 768 - len(vector))])
    return {
        'vector': vector[:768],
        'dim': 768,
        'model_name': 'mock',
        'ai_mode': 'mock',
    }
