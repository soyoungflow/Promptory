import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from prompts.models import Prompt
from tasks.celery_tasks import transform_prompt
from tasks.models import Task

from .models import AgentTransformation, BlueprintDesign
from .serializers import (
    AgentTransformationSerializer,
    SimilarPromptSerializer,
    TaskStatusSerializer,
)
from .services.similarity import find_similar


class TransformPromptView(APIView):
    """POST /api/prompts/<id>/transform/ — author only, async transform."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        prompt = get_object_or_404(Prompt, pk=pk, is_deleted=False)
        if prompt.user_id != request.user.id:
            return Response({'detail': '작성자만 변환을 요청할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        if prompt.prompt_type != 'single_prompt':
            return Response(
                {'detail': '단일 프롬프트만 AI 변환을 사용할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = Task.objects.create(
            task_id=uuid.uuid4(),
            task_type='transform',
            status='PENDING',
            prompt=prompt,
            user=request.user,
        )
        transform_prompt.delay(str(task.task_id), prompt.id)
        return Response({
            'task_id': str(task.task_id),
            'status': 'PENDING',
            'status_url': f'/api/tasks/{task.task_id}/status/',
        }, status=status.HTTP_202_ACCEPTED)


class TaskStatusView(APIView):
    """GET /api/tasks/<task_id>/status/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task = get_object_or_404(Task, task_id=task_id, user=request.user)
        payload = {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'started_at': task.started_at,
            'finished_at': task.finished_at,
            'error_message': task.error_message,
            'result_id': task.result_id,
            'created_at': task.created_at,
        }
        if task.started_at and task.finished_at:
            payload['elapsed_seconds'] = (task.finished_at - task.started_at).total_seconds()
        if task.status == 'SUCCESS' and task.task_type == 'blueprint_design':
            design = BlueprintDesign.objects.filter(source_prompt_id=task.prompt_id).first()
            if design:
                payload['result_url'] = f'/api/blueprints/design/{design.id}/'
        elif task.status == 'SUCCESS' and task.task_type == 'transform':
            payload['result_url'] = f'/api/prompts/{task.prompt_id}/agent/'
        serializer = TaskStatusSerializer(payload)
        return Response(serializer.data)


class AgentDetailView(APIView):
    """GET /api/prompts/<id>/agent/ — latest transformation (JSON for inline UI)."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        latest = AgentTransformation.objects.filter(prompt_id=pk).order_by('-created_at').first()
        if not latest:
            return Response({'detail': '변환 결과가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AgentTransformationSerializer(latest).data)


class SimilarPromptsView(APIView):
    """GET /api/prompts/<id>/similar/"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        get_object_or_404(Prompt, pk=pk, is_deleted=False)
        similar = find_similar(pk, top_k=5)
        return Response(SimilarPromptSerializer(similar, many=True).data)
