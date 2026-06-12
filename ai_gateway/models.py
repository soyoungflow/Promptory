from django.conf import settings
from django.db import models


class BlueprintDesign(models.Model):
    """설계서 만들기 세션 — 기존 프롬프트 등록과 분리된 생성 플로우."""

    STATUS_CHOICES = [
        ('pending', '대기'),
        ('processing', '처리 중'),
        ('success', '완료'),
        ('fail', '실패'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='blueprint_designs', verbose_name='작성자',
    )
    title = models.CharField(max_length=200, blank=True, default='', verbose_name='제목')
    brief = models.TextField(verbose_name='자동화 요청')
    extra_context = models.TextField(blank=True, default='', verbose_name='추가 맥락')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True,
    )
    source_prompt = models.OneToOneField(
        'prompts.Prompt', on_delete=models.CASCADE,
        related_name='blueprint_design', verbose_name='내부 초안 프롬프트',
    )
    transformation = models.OneToOneField(
        'AgentTransformation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='blueprint_design',
        verbose_name='변환 결과',
    )
    recipe = models.ForeignKey(
        'prompts.Prompt', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='from_blueprint_designs',
        verbose_name='등록된 레시피',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '설계서 만들기'
        verbose_name_plural = '설계서 만들기 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        label = self.title or self.brief[:40]
        return f'{self.user_id} — {label}'


class AgentTransformation(models.Model):
    prompt = models.ForeignKey(
        'prompts.Prompt', on_delete=models.CASCADE, related_name='transformations',
    )
    decomposed_steps = models.JSONField(default=list)
    suggested_tools = models.JSONField(default=list)
    system_messages = models.JSONField(default=list)
    confidence_score = models.FloatField(default=0.0)
    model_used = models.CharField(max_length=100, default='')
    ai_mode = models.CharField(
        max_length=10,
        default='mock',
        choices=[('mock', 'mock'), ('real', 'real')],
        verbose_name='AI 실행 모드',
    )
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
    quality_strategy_summary = models.CharField(
        max_length=200, blank=True, default='', verbose_name='검증 전략 요약',
    )
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
