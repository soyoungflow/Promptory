from django.db import models


class AgentTransformation(models.Model):
    prompt = models.ForeignKey(
        'prompts.Prompt', on_delete=models.CASCADE, related_name='transformations',
    )
    decomposed_steps = models.JSONField(default=list)
    suggested_tools = models.JSONField(default=list)
    system_messages = models.JSONField(default=list)
    confidence_score = models.FloatField(default=0.0)
    model_used = models.CharField(max_length=100, default='')
    overall_pattern = models.CharField(
        max_length=20,
        default='Sequential',
        choices=[
            ('Sequential', 'Sequential'),
            ('ReAct', 'ReAct'),
            ('Reflection', 'Reflection'),
            ('MultiAgent', 'Multi-agent'),
        ],
    )
    context_strategy_summary = models.CharField(max_length=200, blank=True, default='')
    harness_strategy_summary = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '에이전트 변환 결과'
        verbose_name_plural = '에이전트 변환 결과 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prompt', '-created_at']),
            models.Index(fields=['overall_pattern']),
        ]

    def __str__(self):
        return f'{self.prompt_id} — {self.created_at:%Y-%m-%d %H:%M}'


class PromptEmbedding(models.Model):
    prompt = models.OneToOneField(
        'prompts.Prompt', on_delete=models.CASCADE, related_name='embedding',
    )
    vector = models.JSONField()
    model_name = models.CharField(max_length=100, default='jhgan/ko-sroberta-multitask')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '프롬프트 임베딩'
        verbose_name_plural = '프롬프트 임베딩 목록'

    def __str__(self):
        return f'embedding:{self.prompt_id}'
