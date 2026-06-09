from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TransformRequest(BaseModel):
    prompt_text: str = Field(..., min_length=10, max_length=10000)
    max_steps: int = Field(default=4, ge=2, le=8)


class ContextPolicy(BaseModel):
    previous_output_strategy: Literal[
        'full', 'summarize_500', 'selective', 'vector_query', 'none',
    ] = 'full'
    memory_scope: Literal['this_step_only', 'all_previous', 'user_session'] = 'all_previous'
    reason: str = Field(default='', description='왜 이 정책을 선택했는지')


class HarnessPolicy(BaseModel):
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    max_retries: int = Field(default=2, ge=0, le=5)
    fallback_action: Literal['skip_step', 'use_default', 'fail_fast'] = 'skip_step'
    validation_schema: Optional[str] = None
    cost_budget_tokens: int = Field(default=2000, ge=100, le=20000)
    rate_limit: str = Field(default='10/min')


class KnowledgeRef(BaseModel):
    type: Literal['url', 'document', 'dataset', 'api', 'rag_collection'] = 'document'
    source: str = Field(default='', description='자료 출처 식별자')
    usage: Literal['always', 'if_needed', 'fallback'] = 'always'
    description: str = Field(default='', description='이 자료가 왜 필요한지 한 줄')


class VerificationCriteria(BaseModel):
    success_signals: List[str] = Field(
        default_factory=list,
        description="성공 신호 (예: 'URL 5개 이상', 'H2 3개 포함')",
    )
    failure_signals: List[str] = Field(
        default_factory=list,
        description="실패 신호 (예: 'TODO 단어 포함', '100자 미만')",
    )
    evaluator: Literal['rule', 'llm_judge', 'human', 'none'] = 'rule'
    min_quality_score: float = Field(default=0.7, ge=0.0, le=1.0)
    on_fail: Literal['retry', 'skip', 'escalate'] = 'retry'


class StepSpec(BaseModel):
    step: int
    name: str
    system_message: str
    tool: str = ''
    context_policy: ContextPolicy = Field(default_factory=ContextPolicy)
    harness_policy: HarnessPolicy = Field(default_factory=HarnessPolicy)
    knowledge_refs: List[KnowledgeRef] = Field(default_factory=list)
    verification_criteria: VerificationCriteria = Field(default_factory=VerificationCriteria)


class TransformResponse(BaseModel):
    decomposed_steps: List[StepSpec]
    suggested_tools: List[str]
    system_messages: List[str]
    confidence_score: float
    model_used: str
    overall_pattern: Literal['Sequential', 'ReAct', 'Reflection', 'MultiAgent'] = 'Sequential'
    context_strategy_summary: str = Field(default='', description='전체 컨텍스트 전략 한 줄 요약')
    harness_strategy_summary: str = Field(default='', description='전체 하네스 전략 한 줄 요약')
    quality_strategy_summary: str = Field(default='', description='전체 검증 전략 한 줄 요약')


class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class EmbedResponse(BaseModel):
    vector: List[float]
    dim: int
    model_name: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    provider: str
