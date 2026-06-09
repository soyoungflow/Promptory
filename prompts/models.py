from django.db import models
from django.conf import settings
from django.utils import timezone
from .managers import SoftDeleteManager


class Category(models.Model):
    """단일 프롬프트용 AI 벤더 카테고리 (ChatGPT, Claude 등)."""
    name        = models.CharField(max_length=50, unique=True, verbose_name='카테고리명')
    slug        = models.SlugField(max_length=50, unique=True, verbose_name='슬러그')
    description = models.TextField(blank=True, verbose_name='설명')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '카테고리'
        verbose_name_plural = '카테고리 목록'
        ordering            = ['name']

    def __str__(self):
        return self.name


class RecipeCategory(models.Model):
    """에이전트 레시피용 주제 카테고리 (작성자가 직접 입력·생성)."""
    name       = models.CharField(max_length=50, unique=True, verbose_name='레시피 카테고리명')
    slug       = models.SlugField(max_length=50, unique=True, verbose_name='슬러그')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '레시피 카테고리'
        verbose_name_plural = '레시피 카테고리 목록'
        ordering            = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name       = models.CharField(max_length=50, unique=True, verbose_name='태그명')
    slug       = models.SlugField(max_length=50, unique=True, verbose_name='슬러그')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = '태그'
        verbose_name_plural = '태그 목록'
        ordering            = ['name']

    def __str__(self):
        return self.name


class Prompt(models.Model):
    PROMPT_TYPE_CHOICES = [
        ('single_prompt', '단일 프롬프트'),
        ('agent_recipe', '에이전트 레시피'),
        ('mcp_package', 'MCP 패키지'),
    ]
    AGENT_PATTERN_CHOICES = [
        ('', '해당 없음'),
        ('sequential', 'Sequential'),
        ('react', 'ReAct'),
        ('reflection', 'Reflection'),
        ('multi_agent', 'Multi-agent'),
    ]

    AI_MODEL_CHOICES = [
        ('gpt-5-5',          'GPT-5.5'),
        ('gpt-5-5-instant',  'GPT-5.5 Instant'),
        ('claude-opus-4-7',  'Claude Opus 4.7'),
        ('claude-sonnet-4-6','Claude Sonnet 4.6'),
        ('gemini-3-1-pro',   'Gemini 3.1 Pro'),
        ('gemini-3-0-flash', 'Gemini 3.0 Flash'),
        ('other',            '기타'),
    ]

    user     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='prompts', verbose_name='작성자')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='prompts', verbose_name='카테고리')
    recipe_category = models.ForeignKey(
        RecipeCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='prompts', verbose_name='레시피 카테고리',
    )
    tags     = models.ManyToManyField(Tag, blank=True, related_name='prompts', verbose_name='태그')

    title       = models.CharField(max_length=200, verbose_name='제목')
    content     = models.TextField(verbose_name='프롬프트 본문')
    description = models.TextField(blank=True, verbose_name='설명')
    ai_model    = models.CharField(max_length=30, choices=AI_MODEL_CHOICES,
                                   default='other', verbose_name='AI 모델')

    is_free = models.BooleanField(default=True, verbose_name='무료 여부')
    price   = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, verbose_name='가격')

    view_count = models.PositiveIntegerField(default=0, verbose_name='조회수')

    prompt_type = models.CharField(
        max_length=20, choices=PROMPT_TYPE_CHOICES,
        default='single_prompt', verbose_name='프롬프트 유형',
    )
    workflow_steps = models.JSONField(default=list, blank=True, verbose_name='워크플로우 단계')
    agent_pattern = models.CharField(
        max_length=20, choices=AGENT_PATTERN_CHOICES,
        blank=True, default='', verbose_name='에이전트 패턴',
    )

    # 설계서 만들기 도구 내부 초안 (탐색·목록에서 제외)
    is_blueprint_draft = models.BooleanField(default=False, db_index=True, verbose_name='설계 초안')

    # Soft Delete
    is_deleted = models.BooleanField(default=False, db_index=True, verbose_name='삭제 여부')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='삭제 일시')
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='deleted_prompts', verbose_name='삭제한 사용자')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    # Manager: 기본은 살아있는 항목만, 관리자용은 all_with_deleted()
    objects     = SoftDeleteManager()
    all_objects = models.Manager()   # admin에서 전체 접근용

    class Meta:
        verbose_name        = '프롬프트'
        verbose_name_plural = '프롬프트 목록'
        ordering            = ['-created_at']

    def __str__(self):
        return self.title

    def soft_delete(self, user=None):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class PromptFile(models.Model):
    prompt    = models.ForeignKey(Prompt, on_delete=models.CASCADE,
                                  related_name='files', verbose_name='프롬프트')
    file      = models.FileField(upload_to='prompts/%Y/%m/%d/', verbose_name='파일')
    file_name = models.CharField(max_length=255, verbose_name='원본 파일명')
    file_type = models.CharField(max_length=50,  verbose_name='파일 타입')
    file_size = models.PositiveIntegerField(verbose_name='파일 크기(bytes)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드 일시')

    class Meta:
        verbose_name        = '프롬프트 파일'
        verbose_name_plural = '프롬프트 파일 목록'

    def __str__(self):
        return f"{self.prompt.title} — {self.file_name}"
