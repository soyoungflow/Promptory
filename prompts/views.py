from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q

from .models import Category, Tag, Prompt, PromptFile
from .serializers import (
    CategorySerializer, TagSerializer,
    PromptListSerializer, PromptDetailSerializer,
    PromptWriteSerializer, PromptFileSerializer,
)
from .permissions import IsAuthorOrReadOnly
from .filters import PromptFilter


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """카테고리 목록 / 상세 (읽기 전용)"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """태그 목록 / 상세"""
    queryset = Tag.objects.annotate(
        prompt_count=Count('prompts', filter=Q(prompts__is_deleted=False), distinct=True)
    )
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    search_fields = ['name', 'slug']

    @action(detail=True, methods=['get'], url_path='prompts')
    def prompts(self, request, slug=None):
        """GET /api/tags/{slug}/prompts/ — 태그별 프롬프트"""
        tag = self.get_object()
        qs = Prompt.objects.filter(tags=tag, is_deleted=False)
        serializer = PromptListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='popular')
    def popular(self, request):
        """GET /api/tags/popular/ — 사용량 기준 인기 태그"""
        try:
            limit = int(request.query_params.get('limit', 10))
        except (TypeError, ValueError):
            limit = 10
        limit = max(1, min(limit, 30))
        qs = self.get_queryset().filter(prompt_count__gt=0).order_by('-prompt_count', 'name')[:limit]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class PromptViewSet(viewsets.ModelViewSet):
    """
    프롬프트 CRUD + 파일업로드 + 필터/검색/페이지네이션.
    - list  : 목록 (PromptListSerializer)
    - create: 생성 (PromptWriteSerializer)
    - retrieve: 상세 (PromptDetailSerializer) + view_count +1
    - update/partial_update: 수정 (IsAuthorOrReadOnly)
    - destroy: Soft Delete (IsAuthorOrReadOnly)
    """
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PromptFilter
    search_fields = ['title', 'description']      # ?search= 검색 대상 필드
    ordering_fields = ['created_at', 'view_count', 'price']
    ordering = ['-created_at']

    def get_queryset(self):
        # Soft Delete 된 항목 제외
        return Prompt.objects.filter(is_deleted=False).select_related(
            'user', 'category'
        ).prefetch_related('tags', 'files', 'likes', 'bookmarks')

    def get_serializer_class(self):
        if self.action == 'list':
            return PromptListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return PromptWriteSerializer
        return PromptDetailSerializer

    def perform_create(self, serializer):
        # 작성자를 현재 로그인 사용자로 자동 지정
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 조회수 +1
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """DELETE → Soft Delete (물리 삭제 금지)"""
        instance = self.get_object()
        instance.soft_delete(user=request.user)
        return Response({'detail': '삭제되었습니다.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def files(self, request, pk=None):
        """POST /api/prompts/{id}/files/ — 파일 업로드"""
        prompt = self.get_object()
        serializer = PromptFileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(prompt=prompt)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
