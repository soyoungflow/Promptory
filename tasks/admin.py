from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'task_type', 'status', 'prompt', 'user', 'created_at', 'finished_at')
    list_filter = ('status', 'task_type', 'created_at')
    search_fields = ('task_id', 'prompt__title', 'user__email')
    readonly_fields = ('task_id', 'created_at', 'started_at', 'finished_at')
