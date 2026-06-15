from rest_framework import serializers

from .models import AgentTransformation, BlueprintDesign


class TransformEnqueueSerializer(serializers.Serializer):
    blueprint_design_id = serializers.IntegerField(required=False, allow_null=True)


class AgentTransformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTransformation
        fields = (
            'id', 'prompt', 'decomposed_steps', 'suggested_tools',
            'system_messages', 'confidence_score', 'model_used', 'ai_mode',
            'created_at', 'overall_pattern', 'context_strategy_summary',
            'harness_strategy_summary', 'quality_strategy_summary',
        )


class TaskStatusSerializer(serializers.Serializer):
    task_id = serializers.UUIDField()
    task_type = serializers.CharField()
    status = serializers.CharField()
    ai_mode = serializers.CharField(required=False, allow_blank=True)
    started_at = serializers.DateTimeField(allow_null=True)
    finished_at = serializers.DateTimeField(allow_null=True)
    error_message = serializers.CharField(allow_blank=True)
    result_id = serializers.IntegerField(allow_null=True)
    created_at = serializers.DateTimeField()
    result_url = serializers.CharField(required=False, allow_blank=True)
    elapsed_seconds = serializers.FloatField(required=False, allow_null=True)


class SimilarPromptSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    prompt_type = serializers.CharField(required=False, allow_blank=True)
    agent_pattern = serializers.CharField(required=False, allow_blank=True)
    similarity = serializers.FloatField()


class BlueprintDesignCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')
    brief = serializers.CharField(min_length=10)
    extra_context = serializers.CharField(required=False, allow_blank=True, default='')


class BlueprintPublishRecipeSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    recipe_category_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, default='')


class BlueprintDesignSerializer(serializers.ModelSerializer):
    transformation = AgentTransformationSerializer(read_only=True)

    class Meta:
        model = BlueprintDesign
        fields = (
            'id', 'title', 'brief', 'extra_context', 'status',
            'source_prompt_id', 'transformation', 'recipe', 'created_at', 'updated_at',
        )
        read_only_fields = fields


class MyTransformationSerializer(serializers.Serializer):
    design_id = serializers.IntegerField(required=False, allow_null=True)
    recipe_id = serializers.IntegerField(required=False, allow_null=True)
    design_status = serializers.CharField(required=False, allow_blank=True)
    prompt_id = serializers.IntegerField()
    prompt_title = serializers.CharField()
    transformation_id = serializers.IntegerField()
    decomposed_steps = serializers.JSONField()
    suggested_tools = serializers.JSONField()
    confidence_score = serializers.FloatField()
    model_used = serializers.CharField()
    ai_mode = serializers.CharField(required=False, allow_blank=True)
    overall_pattern = serializers.CharField(required=False, allow_blank=True)
    context_strategy_summary = serializers.CharField(required=False, allow_blank=True)
    harness_strategy_summary = serializers.CharField(required=False, allow_blank=True)
    quality_strategy_summary = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField()
    task_id = serializers.UUIDField(allow_null=True)
