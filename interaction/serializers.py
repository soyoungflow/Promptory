from rest_framework import serializers
from .models import Comment, Like, Bookmark


class ReplySerializer(serializers.ModelSerializer):
    """대댓글용 (중첩)"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    author = serializers.StringRelatedField(source='user')

    class Meta:
        model = Comment
        fields = ('id', 'user_id', 'author', 'content', 'is_deleted', 'created_at')


class CommentSerializer(serializers.ModelSerializer):
    """댓글 + 대댓글 포함"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    author = serializers.StringRelatedField(source='user')
    replies = ReplySerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = (
            'id', 'user_id', 'author', 'content', 'parent', 'replies',
            'is_deleted', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'user_id', 'author', 'replies',
            'is_deleted', 'created_at', 'updated_at',
        )

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError('댓글 내용을 입력해주세요.')
        return value


class MyCommentSerializer(serializers.ModelSerializer):
    """보관함 — 내 댓글 목록 (프롬프트 맥락 포함)"""

    prompt_id = serializers.IntegerField(source='prompt.id', read_only=True)
    prompt_title = serializers.CharField(source='prompt.title', read_only=True)

    class Meta:
        model = Comment
        fields = (
            'id', 'content', 'parent', 'prompt_id', 'prompt_title',
            'created_at', 'updated_at',
        )


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('id', 'prompt', 'user', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ('id', 'prompt', 'user', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
