import hashlib
import struct

from schemas import (
    ContextPolicy,
    EmbedResponse,
    HarnessPolicy,
    KnowledgeRef,
    StepSpec,
    TransformResponse,
    VerificationCriteria,
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
        knowledge_refs=[
            KnowledgeRef(
                type='api', source='네이버 블로그 검색 API',
                usage='always', description='국내 최신 트렌드 확보',
            ),
            KnowledgeRef(
                type='api', source='구글 학술 검색',
                usage='if_needed', description='학술적 근거 필요 시',
            ),
        ],
        verification_criteria=VerificationCriteria(
            success_signals=['URL 5개 이상 수집', '발행일 1년 이내', '서로 다른 출처 3개 이상'],
            failure_signals=['검색 결과 0건', '동일 도메인만 반환'],
            evaluator='rule',
            min_quality_score=0.7,
            on_fail='retry',
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
        knowledge_refs=[
            KnowledgeRef(
                type='document', source='SEO 키워드 베스트프랙티스',
                usage='always', description='SEO 친화적 헤딩 구조',
            ),
        ],
        verification_criteria=VerificationCriteria(
            success_signals=['H2 3개 이상', '각 H2 아래 H3 2개 이상', '논리적 흐름'],
            failure_signals=['헤딩 없음', '계층 깨짐'],
            evaluator='rule',
            min_quality_score=0.75,
            on_fail='retry',
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
        knowledge_refs=[
            KnowledgeRef(
                type='document', source='브랜드 톤매뉴얼.pdf',
                usage='always', description='일관된 브랜드 보이스 유지',
            ),
        ],
        verification_criteria=VerificationCriteria(
            success_signals=['섹션당 300자 이상', '브랜드 톤 일치', '키워드 자연 삽입'],
            failure_signals=['Lorem ipsum 포함', 'TODO 포함', '반복 문장'],
            evaluator='llm_judge',
            min_quality_score=0.7,
            on_fail='retry',
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
        knowledge_refs=[
            KnowledgeRef(
                type='api', source='맞춤법 검사 API',
                usage='always', description='문법 오류 자동 검출',
            ),
            KnowledgeRef(
                type='dataset', source='팩트체크 데이터셋',
                usage='if_needed', description='주장 검증',
            ),
        ],
        verification_criteria=VerificationCriteria(
            success_signals=['수정 제안 1개 이상', '각 제안에 근거', '문법 오류 0건'],
            failure_signals=['수정 사항 없음으로 응답', '근거 없는 제안'],
            evaluator='llm_judge',
            min_quality_score=0.8,
            on_fail='escalate',
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
        quality_strategy_summary='리서치는 규칙 검증, 초안/검토는 LLM judge로 품질 0.7~0.8 보장',
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
