from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ai_gateway.models import AgentTransformation
from ai_gateway.serializers import MyTransformationSerializer
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
            # 가입 즉시 JWT 발급
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
            token.blacklist()  # simplejwt 블랙리스트
            return Response({'detail': '로그아웃 되었습니다.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'detail': '유효하지 않은 토큰입니다.'}, status=status.HTTP_400_BAD_REQUEST)


class MyPromptListView(APIView):
    """GET /api/accounts/me/prompts/ — 내가 등록한 프롬프트 목록 (삭제 제외)"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Prompt.objects.filter(user=request.user, is_deleted=False).select_related(
            'user', 'category'
        ).prefetch_related('tags', 'likes', 'bookmarks')
        serializer = PromptListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class MyTransformationListView(APIView):
    """GET /api/accounts/me/transformations/ — owned prompts, latest transform each."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prompts = Prompt.objects.filter(user=request.user, is_deleted=False).order_by('-created_at')
        rows = []
        for prompt in prompts:
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
                'created_at': latest.created_at,
                'task_id': latest_task.task_id if latest_task else None,
            })
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
