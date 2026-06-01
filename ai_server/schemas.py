from typing import List

from pydantic import BaseModel, Field


class TransformRequest(BaseModel):
    prompt_text: str = Field(..., min_length=10, max_length=10000)
    max_steps: int = Field(default=4, ge=2, le=8)


class StepSpec(BaseModel):
    step: int
    name: str
    system_message: str
    tool: str = ''


class TransformResponse(BaseModel):
    decomposed_steps: List[StepSpec]
    suggested_tools: List[str]
    system_messages: List[str]
    confidence_score: float
    model_used: str


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
