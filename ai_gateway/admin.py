from django.contrib import admin

from .models import AgentTransformation, BlueprintDesign, PromptEmbedding


@admin.register(BlueprintDesign)
class BlueprintDesignAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'status', 'recipe', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'brief', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


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
