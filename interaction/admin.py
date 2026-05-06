from django.contrib import admin
from django.utils.html import format_html
from .models import Comment, Like, Bookmark


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ('short_content', 'user', 'prompt', 'depth', 'deleted_status', 'created_at')
    list_filter   = ('is_deleted',)
    search_fields = ('content', 'user__email', 'prompt__title')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')

    def get_queryset(self, request):
        # 관리자는 삭제된 댓글도 볼 수 있음
        return Comment.all_objects.all().select_related('user', 'prompt', 'parent')

    def short_content(self, obj):
        return obj.content[:40] + ('...' if len(obj.content) > 40 else '')
    short_content.short_description = '내용'

    def depth(self, obj):
        return format_html('<span style="color:#6b7280;font-size:11px;">{}</span>',
                           '대댓글' if obj.parent else '댓글')
    depth.short_description = '유형'

    def deleted_status(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color:#b91c1c;font-size:11px;">삭제됨</span>')
        return format_html('<span style="color:#065f46;font-size:11px;">정상</span>')
    deleted_status.short_description = '상태'

    actions = ['action_soft_delete', 'action_restore']

    def action_soft_delete(self, request, queryset):
        count = 0
        for obj in queryset.filter(is_deleted=False):
            obj.soft_delete()
            count += 1
        self.message_user(request, f'{count}개 댓글을 삭제 처리했습니다.')
    action_soft_delete.short_description = '선택 댓글 Soft Delete'

    def action_restore(self, request, queryset):
        count = queryset.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)
        self.message_user(request, f'{count}개 댓글을 복구했습니다.')
    action_restore.short_description = '선택 댓글 복구'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display  = ('user', 'prompt', 'created_at')
    search_fields = ('user__email', 'prompt__title')
    raw_id_fields = ('user', 'prompt')


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display  = ('user', 'prompt', 'created_at')
    search_fields = ('user__email', 'prompt__title')
    raw_id_fields = ('user', 'prompt')
