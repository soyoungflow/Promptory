from rest_framework import serializers

from .models import AgentTransformation


class AgentTransformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTransformation
        fields = (
            'id', 'prompt', 'decomposed_steps', 'suggested_tools',
            'system_messages', 'confidence_score', 'model_used', 'created_at',
            'overall_pattern', 'context_strategy_summary', 'harness_strategy_summary',
            'quality_strategy_summary',
        )


class TaskStatusSerializer(serializers.Serializer):
    task_id = serializers.UUIDField()
    task_type = serializers.CharField()
    status = serializers.CharField()
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


class MyTransformationSerializer(serializers.Serializer):
    prompt_id = serializers.IntegerField()
    prompt_title = serializers.CharField()
    transformation_id = serializers.IntegerField()
    decomposed_steps = serializers.JSONField()
    suggested_tools = serializers.JSONField()
    confidence_score = serializers.FloatField()
    model_used = serializers.CharField()
    overall_pattern = serializers.CharField(required=False, allow_blank=True)
    context_strategy_summary = serializers.CharField(required=False, allow_blank=True)
    harness_strategy_summary = serializers.CharField(required=False, allow_blank=True)
    quality_strategy_summary = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField()
    task_id = serializers.UUIDField(allow_null=True)
