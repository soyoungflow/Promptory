import hashlib
import struct

from schemas import EmbedResponse, StepSpec, TransformResponse

MOCK_STEPS = [
    StepSpec(step=1, name='리서치', system_message='주제 관련 최신 정보를 수집하세요.', tool='web_search'),
    StepSpec(step=2, name='개요', system_message='H2/H3 구조로 개요를 작성하세요.', tool='outline_generator'),
    StepSpec(step=3, name='초안', system_message='섹션별 본문을 작성하세요.', tool='text_generation'),
    StepSpec(step=4, name='검토', system_message='문법·사실·일관성을 점검하세요.', tool='reflection'),
]


def mock_transform(prompt_text: str) -> TransformResponse:
    return TransformResponse(
        decomposed_steps=MOCK_STEPS,
        suggested_tools=['web_search', 'outline_generator', 'text_generation', 'reflection'],
        system_messages=[step.system_message for step in MOCK_STEPS],
        confidence_score=0.92,
        model_used='mock',
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
