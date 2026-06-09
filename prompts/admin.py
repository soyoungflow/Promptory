from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, RecipeCategory, Tag, Prompt, PromptFile


@admin.register(RecipeCategory)
class RecipeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def recipe_count(self, obj):
        return obj.prompts.filter(is_deleted=False, prompt_type='agent_recipe').count()
    recipe_count.short_description = '레시피 수'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'slug', 'prompt_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def prompt_count(self, obj):
        return obj.prompts.count()
    prompt_count.short_description = '프롬프트 수'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display  = ('name', 'slug', 'prompt_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def prompt_count(self, obj):
        return obj.prompts.count()
    prompt_count.short_description = '프롬프트 수'


class PromptFileInline(admin.TabularInline):
    model          = PromptFile
    extra          = 0
    readonly_fields = ('file_name', 'file_type', 'file_size_display', 'created_at')
    fields         = ('file', 'file_name', 'file_type', 'file_size_display', 'created_at')

    def file_size_display(self, obj):
        if obj.file_size:
            return f"{obj.file_size / 1024:.1f} KB"
        return '-'
    file_size_display.short_description = '파일 크기'


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    # ── 목록 화면 ──
    list_display = (
        'title', 'user', 'category', 'recipe_category', 'ai_model', 'prompt_type',
        'is_free_badge', 'view_count',
        'like_count', 'comment_count',
        'deleted_status', 'created_at',
    )
    list_filter  = ('is_deleted', 'is_free', 'ai_model', 'category')
    search_fields = ('title', 'content', 'user__email')
    date_hierarchy = 'created_at'
    ordering      = ('-created_at',)

    # ── 상세 화면 ──
    readonly_fields = (
        'view_count', 'created_at', 'updated_at',
        'deleted_at', 'deleted_by',
    )
    filter_horizontal = ('tags',)
    inlines = [PromptFileInline]

    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'title', 'description', 'content', 'ai_model', 'category', 'tags')
        }),
        ('판매 설정', {
            'fields': ('is_free', 'price'),
            'classes': ('collapse',),
        }),
        ('통계', {
            'fields': ('view_count',),
            'classes': ('collapse',),
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',),
            'description': '⚠️ 물리 삭제 금지. 아래 액션을 통해 Soft Delete / 복구를 사용하세요.',
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # 관리자에서 삭제된 항목 포함 전체 조회
    def get_queryset(self, request):
        return Prompt.all_objects.all().select_related(
            'user', 'category', 'deleted_by'
        ).prefetch_related('tags', 'likes', 'comments')

    # ── 커스텀 컬럼 ──
    def is_free_badge(self, obj):
        if obj.is_free:
            return format_html('<span style="color:#065f46;background:#d1fae5;padding:2px 8px;border-radius:12px;font-size:11px;">무료</span>')
        return format_html('<span style="color:#92400e;background:#fef3c7;padding:2px 8px;border-radius:12px;font-size:11px;">₩{}</span>', f"{obj.price:,.0f}")
    is_free_badge.short_description = '가격'

    def deleted_status(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color:#b91c1c;background:#fef2f2;padding:2px 8px;border-radius:12px;font-size:11px;">삭제됨</span>')
        return format_html('<span style="color:#065f46;background:#d1fae5;padding:2px 8px;border-radius:12px;font-size:11px;">정상</span>')
    deleted_status.short_description = '상태'

    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = '좋아요'

    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = '댓글'

    # ── 액션 ──
    actions = ['action_soft_delete', 'action_restore']

    def get_actions(self, request):
        """
        Django/admin 커스터마이징이나 상속 상태에 따라
        동일 액션이 중복 표시되는 경우를 방지한다.
        """
        actions = super().get_actions(request)
        deduped = {}
        seen = set()
        for key, value in actions.items():
            func, name, desc = value
            token = (name, desc)
            if token in seen:
                continue
            seen.add(token)
            deduped[key] = value
        return deduped

    def action_soft_delete(self, request, queryset):
        count = 0
        for obj in queryset.filter(is_deleted=False):
            obj.soft_delete(user=request.user)
            count += 1
        self.message_user(request, f'{count}개 항목을 Soft Delete 처리했습니다.')
    action_soft_delete.short_description = '선택 항목 Soft Delete (복구 가능)'

    def action_restore(self, request, queryset):
        count = 0
        for obj in queryset.filter(is_deleted=True):
            obj.restore()
            count += 1
        self.message_user(request, f'{count}개 항목을 복구했습니다.')
    action_restore.short_description = '선택 항목 복구'
