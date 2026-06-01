from django.contrib import admin

from .models import AgentTransformation, PromptEmbedding


@admin.register(AgentTransformation)
class AgentTransformationAdmin(admin.ModelAdmin):
    list_display = ('id', 'prompt', 'confidence_score', 'model_used', 'created_at')
    list_filter = ('model_used', 'created_at')
    search_fields = ('prompt__title',)
    readonly_fields = ('created_at',)


@admin.register(PromptEmbedding)
class PromptEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('id', 'prompt', 'model_name', 'created_at')
    readonly_fields = ('vector', 'created_at')
