from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('email', 'username', 'is_staff', 'is_active', 'deleted_status', 'date_joined')
    list_filter   = ('is_staff', 'is_active', 'is_deleted')
    search_fields = ('email', 'username')
    ordering      = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('추가 정보', {
            'fields': ('bio', 'avatar')
        }),
        ('계정 상태', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('deleted_at',)

    def deleted_status(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color:#b91c1c;font-size:11px;">탈퇴</span>')
        return format_html('<span style="color:#065f46;font-size:11px;">활성</span>')
    deleted_status.short_description = '상태'
