from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ai_gateway.models import AgentTransformation, BlueprintDesign
from ai_gateway.serializers import MyTransformationSerializer
from ai_gateway.services.blueprint import sync_design_from_task
from prompts.models import Prompt
from prompts.serializers import PromptListSerializer
from tasks.models import Task

from .serializers import RegisterSerializer, UserProfileSerializer

User = get_user_model()


class RegisterView(APIView):
    """POST /api/accounts/register/ — 회원가입"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': RegisterSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """POST /api/accounts/logout/ — Refresh Token 블랙리스트 처리"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': '로그아웃 되었습니다.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'detail': '유효하지 않은 토큰입니다.'}, status=status.HTTP_400_BAD_REQUEST)


class MyPromptListView(APIView):
    """GET /api/accounts/me/prompts/ — 내가 등록한 프롬프트 목록 (삭제 제외)"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Prompt.objects.filter(
            user=request.user, is_deleted=False, is_blueprint_draft=False,
        ).select_related(
            'user', 'category'
        ).prefetch_related('tags', 'likes', 'bookmarks')
        serializer = PromptListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class MyTransformationListView(APIView):
    """GET /api/accounts/me/transformations/ — 설계서 만들기(BlueprintDesign) 목록."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        designs = (
            BlueprintDesign.objects.filter(user=request.user)
            .select_related('transformation', 'recipe', 'source_prompt')
            .order_by('-created_at')
        )
        rows = []
        seen_design_ids = set()

        for design in designs:
            design = sync_design_from_task(design)
            seen_design_ids.add(design.id)

            if design.status != 'success' or not design.transformation_id:
                continue

            transformation = design.transformation
            latest_task = Task.objects.filter(
                prompt_id=design.source_prompt_id,
                task_type='blueprint_design',
                status='SUCCESS',
                result_id=transformation.id,
            ).order_by('-finished_at').first()

            display_title = design.title or (design.brief or '')[:80]
            if design.recipe_id and design.recipe:
                display_title = design.recipe.title

            rows.append({
                'design_id': design.id,
                'recipe_id': design.recipe_id,
                'design_status': design.status,
                'prompt_id': design.recipe_id or design.source_prompt_id,
                'prompt_title': display_title,
                'transformation_id': transformation.id,
                'decomposed_steps': transformation.decomposed_steps,
                'suggested_tools': transformation.suggested_tools,
                'confidence_score': transformation.confidence_score,
                'model_used': transformation.model_used,
                'overall_pattern': transformation.overall_pattern,
                'context_strategy_summary': transformation.context_strategy_summary,
                'harness_strategy_summary': transformation.harness_strategy_summary,
                'quality_strategy_summary': transformation.quality_strategy_summary,
                'created_at': transformation.created_at,
                'task_id': latest_task.task_id if latest_task else None,
            })

        # 레거시: 상세 페이지 transform (task_type=transform) 이력
        legacy_prompts = Prompt.objects.filter(
            user=request.user, is_deleted=False, is_blueprint_draft=False,
        ).exclude(
            blueprint_design__isnull=False,
        ).order_by('-created_at')

        for prompt in legacy_prompts:
            latest = AgentTransformation.objects.filter(prompt=prompt).order_by('-created_at').first()
            if not latest:
                continue
            latest_task = Task.objects.filter(
                prompt=prompt,
                task_type='transform',
                status='SUCCESS',
                result_id=latest.id,
            ).order_by('-finished_at').first()
            rows.append({
                'design_id': None,
                'recipe_id': None,
                'design_status': 'success',
                'prompt_id': prompt.id,
                'prompt_title': prompt.title,
                'transformation_id': latest.id,
                'decomposed_steps': latest.decomposed_steps,
                'suggested_tools': latest.suggested_tools,
                'confidence_score': latest.confidence_score,
                'model_used': latest.model_used,
                'overall_pattern': latest.overall_pattern,
                'context_strategy_summary': latest.context_strategy_summary,
                'harness_strategy_summary': latest.harness_strategy_summary,
                'quality_strategy_summary': latest.quality_strategy_summary,
                'created_at': latest.created_at,
                'task_id': latest_task.task_id if latest_task else None,
            })

        rows.sort(key=lambda row: row['created_at'], reverse=True)
        serializer = MyTransformationSerializer(rows, many=True)
        return Response(serializer.data)


class MeView(APIView):
    """GET / PATCH /api/accounts/me/ — 내 프로필"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
