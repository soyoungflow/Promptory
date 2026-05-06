from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from prompts.models import Prompt
from .models import Comment, Like, Bookmark
from .serializers import CommentSerializer, BookmarkSerializer, MyCommentSerializer


class CommentListCreateView(APIView):
    """GET / POST /api/prompts/{prompt_id}/comments/"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, prompt_id):
        prompt = get_object_or_404(Prompt, pk=prompt_id, is_deleted=False)
        # 최상위 댓글만 조회 (replies는 Serializer 중첩으로 포함됨)
        comments = Comment.objects.filter(
            prompt=prompt, parent=None, is_deleted=False
        ).select_related('user').prefetch_related('replies__user')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, prompt_id):
        prompt = get_object_or_404(Prompt, pk=prompt_id, is_deleted=False)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(prompt=prompt, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDeleteView(APIView):
    """DELETE /api/comments/{id}/ — Soft Delete"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        if comment.user != request.user:
            return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        comment.soft_delete()
        return Response({'detail': '삭제되었습니다.'}, status=status.HTTP_200_OK)


class LikeToggleView(APIView):
    """POST /api/prompts/{prompt_id}/like/ — 좋아요 토글"""
    permission_classes = [IsAuthenticated]

    def post(self, request, prompt_id):
        prompt = get_object_or_404(Prompt, pk=prompt_id, is_deleted=False)
        like, created = Like.objects.get_or_create(prompt=prompt, user=request.user)
        if not created:
            # 이미 좋아요 → 취소
            like.delete()
            return Response({
                'liked': False,
                'like_count': prompt.likes.count(),
            })
        return Response({
            'liked': True,
            'like_count': prompt.likes.count(),
        }, status=status.HTTP_201_CREATED)


class BookmarkToggleView(APIView):
    """POST /api/prompts/{prompt_id}/bookmark/ — 북마크 토글"""
    permission_classes = [IsAuthenticated]

    def post(self, request, prompt_id):
        prompt = get_object_or_404(Prompt, pk=prompt_id, is_deleted=False)
        bookmark, created = Bookmark.objects.get_or_create(prompt=prompt, user=request.user)
        if not created:
            bookmark.delete()
            return Response({'bookmarked': False})
        return Response({'bookmarked': True}, status=status.HTTP_201_CREATED)


class MyBookmarkListView(APIView):
    """GET /api/accounts/me/bookmarks/ — 내 북마크 목록"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from prompts.serializers import PromptListSerializer
        bookmarked_prompts = Prompt.objects.filter(
            bookmarks__user=request.user, is_deleted=False
        ).select_related('user', 'category').prefetch_related('tags')
        serializer = PromptListSerializer(bookmarked_prompts, many=True, context={'request': request})
        return Response(serializer.data)


class MyLikedPromptListView(APIView):
    """GET /api/accounts/me/likes/ — 좋아요한 프롬프트 목록"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from prompts.serializers import PromptListSerializer
        qs = (
            Prompt.objects.filter(likes__user=request.user, is_deleted=False)
            .select_related('user', 'category')
            .prefetch_related('tags', 'likes', 'bookmarks')
            .order_by('-created_at')
            .distinct()
        )
        serializer = PromptListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class MyCommentListView(APIView):
    """GET /api/accounts/me/comments/ — 내 댓글 목록 (삭제되지 않은 것, 해당 프롬프트가 삭제되지 않은 것)"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        comments = (
            Comment.objects.filter(
                user=request.user,
                is_deleted=False,
                prompt__is_deleted=False,
            )
            .select_related('prompt')
            .order_by('-created_at')
        )
        serializer = MyCommentSerializer(comments, many=True)
        return Response(serializer.data)
