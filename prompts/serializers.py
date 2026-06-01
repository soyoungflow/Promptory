from rest_framework import serializers
from django.utils.text import slugify
from .models import Category, Tag, Prompt, PromptFile


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class TagSerializer(serializers.ModelSerializer):
    prompt_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'prompt_count')


class PromptFileSerializer(serializers.ModelSerializer):
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.txt', '.md', '.zip'}
    ALLOWED_CONTENT_TYPES = {
        'image/jpeg',
        'image/png',
        'application/pdf',
        'text/plain',
        'text/markdown',
        'application/zip',
        'application/x-zip-compressed',
        'application/octet-stream',
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024

    class Meta:
        model = PromptFile
        fields = ('id', 'file', 'file_name', 'file_type', 'file_size', 'created_at')
        read_only_fields = ('id', 'file_name', 'file_type', 'file_size', 'created_at')

    def validate_file(self, value):
        """파일 업로드 정책 검증"""
        file_name = value.name.lower()
        has_allowed_extension = any(
            file_name.endswith(extension) for extension in self.ALLOWED_EXTENSIONS
        )

        if not has_allowed_extension or value.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError('jpg, png, pdf, txt, md, zip 파일만 업로드 가능합니다.')
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError('파일 크기는 10MB를 초과할 수 없습니다.')
        return value

    def create(self, validated_data):
        file = validated_data['file']
        validated_data['file_name'] = file.name
        validated_data['file_type'] = file.content_type
        validated_data['file_size'] = file.size
        return super().create(validated_data)


class PromptListSerializer(serializers.ModelSerializer):
    """목록용 — 가벼운 응답"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    author = serializers.StringRelatedField(source='user')
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    bookmark_count = serializers.IntegerField(source='bookmarks.count', read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Prompt
        fields = (
            'id', 'title', 'description', 'ai_model',
            'prompt_type', 'agent_pattern',
            'user_id', 'author', 'category_name', 'tags',
            'is_free', 'price', 'view_count',
            'like_count', 'bookmark_count', 'is_liked', 'is_bookmarked',
            'created_at',
        )

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.bookmarks.filter(user=request.user).exists()


class PromptDetailSerializer(serializers.ModelSerializer):
    """상세용 — 본문 포함 전체 응답"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    author = serializers.StringRelatedField(source='user')
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    files = PromptFileSerializer(many=True, read_only=True)
    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    bookmark_count = serializers.IntegerField(source='bookmarks.count', read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Prompt
        fields = (
            'id', 'title', 'content', 'description', 'ai_model',
            'prompt_type', 'workflow_steps', 'agent_pattern',
            'user_id', 'author', 'category', 'tags', 'files',
            'is_free', 'price', 'view_count',
            'like_count', 'bookmark_count', 'comment_count', 'is_liked', 'is_bookmarked',
            'created_at', 'updated_at',
        )

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.bookmarks.filter(user=request.user).exists()


class PromptWriteSerializer(serializers.ModelSerializer):
    """생성/수정용"""
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=True,
        allow_null=False,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Prompt
        fields = (
            'id', 'title', 'content', 'description',
            'ai_model', 'category',
            'prompt_type', 'workflow_steps', 'agent_pattern',
            'tag_ids', 'tag_names', 'is_free', 'price',
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        # 유료인데 가격이 0이면 에러
        if not attrs.get('is_free', True) and attrs.get('price', 0) <= 0:
            raise serializers.ValidationError({'price': '유료 프롬프트는 가격을 입력해야 합니다.'})
        return attrs

    def _resolve_tags(self, tag_ids, tag_names):
        tags = list(tag_ids or [])
        existing_ids = {tag.id for tag in tags}

        for raw_name in tag_names or []:
            name = raw_name.strip()
            if not name:
                continue
            slug = slugify(name, allow_unicode=True) or name.lower().replace(' ', '-')
            tag, _ = Tag.objects.get_or_create(slug=slug, defaults={'name': name})
            if tag.id not in existing_ids:
                tags.append(tag)
                existing_ids.add(tag.id)
        return tags

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        tag_names = validated_data.pop('tag_names', [])
        prompt = super().create(validated_data)
        prompt.tags.set(self._resolve_tags(tag_ids, tag_names))
        return prompt

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        tag_names = validated_data.pop('tag_names', None)
        prompt = super().update(instance, validated_data)
        if tag_ids is not None or tag_names is not None:
            prompt.tags.set(self._resolve_tags(tag_ids or [], tag_names or []))
        return prompt
