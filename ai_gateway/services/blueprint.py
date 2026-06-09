"""설계서 만들기 — 입력 조합·레시피 초안 변환."""

from ai_gateway.models import AgentTransformation, BlueprintDesign
from tasks.models import Task

OVERALL_TO_AGENT_PATTERN = {
    'Sequential': 'sequential',
    'ReAct': 'react',
    'Reflection': 'reflection',
    'MultiAgent': 'multi_agent',
}


def compose_design_content(brief: str, extra_context: str = '') -> str:
    brief = (brief or '').strip()
    extra = (extra_context or '').strip()
    if not extra:
        return brief
    return f'{brief}\n\n[추가 맥락]\n{extra}'


def steps_to_workflow(decomposed_steps: list) -> list:
    workflow = []
    for index, step in enumerate(decomposed_steps or [], start=1):
        workflow.append({
            'step': step.get('step', index),
            'name': step.get('name', ''),
            'system_message': step.get('system_message', ''),
            'tool': step.get('tool', ''),
            'code': step.get('code', ''),
        })
    return workflow


def pattern_from_transformation(overall_pattern: str) -> str:
    return OVERALL_TO_AGENT_PATTERN.get(overall_pattern or '', 'sequential')


def sync_design_from_task(design: BlueprintDesign) -> BlueprintDesign:
    """Celery 완료 후 design 상태가 어긋난 경우 Task 결과로 맞춘다."""
    if design.status == 'success' and design.transformation_id:
        return design

    task = (
        Task.objects.filter(
            prompt_id=design.source_prompt_id,
            task_type='blueprint_design',
        )
        .order_by('-created_at')
        .first()
    )
    if not task:
        return design

    if task.status == 'FAIL':
        if design.status != 'fail':
            design.status = 'fail'
            design.save(update_fields=['status', 'updated_at'])
        return design

    if task.status != 'SUCCESS' or not task.result_id:
        return design

    try:
        transformation = AgentTransformation.objects.get(pk=task.result_id)
    except AgentTransformation.DoesNotExist:
        return design

    design.transformation = transformation
    design.status = 'success'
    design.save(update_fields=['transformation', 'status', 'updated_at'])
    return design
