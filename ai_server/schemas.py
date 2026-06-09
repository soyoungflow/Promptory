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


class StepSpec(BaseModel):
    step: int
    name: str
    system_message: str
    tool: str = ''
    context_policy: ContextPolicy = Field(default_factory=ContextPolicy)
    harness_policy: HarnessPolicy = Field(default_factory=HarnessPolicy)


class TransformResponse(BaseModel):
    decomposed_steps: List[StepSpec]
    suggested_tools: List[str]
    system_messages: List[str]
    confidence_score: float
    model_used: str
    overall_pattern: Literal['Sequential', 'ReAct', 'Reflection', 'MultiAgent'] = 'Sequential'
    context_strategy_summary: str = Field(default='', description='전체 컨텍스트 전략 한 줄 요약')
    harness_strategy_summary: str = Field(default='', description='전체 하네스 전략 한 줄 요약')


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
