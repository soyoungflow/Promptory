from rest_framework import serializers
from django.utils.text import slugify
from .models import Category, RecipeCategory, Tag, Prompt, PromptFile


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class RecipeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeCategory
        fields = ('id', 'name', 'slug')


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
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    recipe_category_name = serializers.CharField(
        source='recipe_category.name', read_only=True, default='',
    )
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
            'user_id', 'author', 'category_name', 'recipe_category_name', 'tags',
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
    recipe_category = RecipeCategorySerializer(read_only=True)
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
            'user_id', 'author', 'category', 'recipe_category', 'tags', 'files',
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
        required=False,
        allow_null=True,
    )
    recipe_category_name = serializers.CharField(
        max_length=50, required=False, allow_blank=True, write_only=True,
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
            'ai_model', 'category', 'recipe_category_name',
            'prompt_type', 'workflow_steps', 'agent_pattern',
            'tag_ids', 'tag_names', 'is_free', 'price',
        )
        read_only_fields = ('id',)

    def _normalize_workflow_steps(self, steps):
        if not steps:
            return []
        normalized = []
        for idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                raise serializers.ValidationError({
                    'workflow_steps': '워크플로 단계 형식이 올바르지 않습니다.',
                })
            name = (step.get('name') or '').strip()
            system_message = (step.get('system_message') or '').strip()
            if not name or not system_message:
                raise serializers.ValidationError({
                    'workflow_steps': '각 단계에는 이름과 시스템 메시지가 필요합니다.',
                })
            normalized.append({
                'step': idx,
                'name': name,
                'system_message': system_message,
                'tool': (step.get('tool') or '').strip(),
                'code': (step.get('code') or '').strip(),
            })
        return normalized

    def validate(self, attrs):
        if not attrs.get('is_free', True) and attrs.get('price', 0) <= 0:
            raise serializers.ValidationError({'price': '유료 프롬프트는 가격을 입력해야 합니다.'})

        prompt_type = attrs.get(
            'prompt_type',
            getattr(self.instance, 'prompt_type', 'single_prompt'),
        )
        workflow_steps = attrs.get(
            'workflow_steps',
            getattr(self.instance, 'workflow_steps', []),
        )
        agent_pattern = attrs.get(
            'agent_pattern',
            getattr(self.instance, 'agent_pattern', ''),
        )

        recipe_category_name = (attrs.pop('recipe_category_name', '') or '').strip()

        if prompt_type == 'agent_recipe':
            if not workflow_steps:
                raise serializers.ValidationError({
                    'workflow_steps': '에이전트 레시피는 최소 1개의 워크플로 단계가 필요합니다.',
                })
            if not agent_pattern:
                raise serializers.ValidationError({
                    'agent_pattern': '에이전트 패턴을 선택하세요.',
                })
            if not recipe_category_name and not getattr(
                self.instance, 'recipe_category_id', None,
            ):
                raise serializers.ValidationError({
                    'recipe_category_name': '레시피 카테고리를 입력하세요.',
                })
            attrs['workflow_steps'] = self._normalize_workflow_steps(workflow_steps)
            attrs['category'] = None
            attrs['ai_model'] = 'other'
            if recipe_category_name:
                attrs['recipe_category'] = self._resolve_recipe_category(recipe_category_name)
        elif prompt_type == 'single_prompt':
            if not attrs.get('category') and not getattr(self.instance, 'category_id', None):
                raise serializers.ValidationError({
                    'category': '카테고리를 선택하세요.',
                })
            if not attrs.get('ai_model') and not getattr(self.instance, 'ai_model', None):
                raise serializers.ValidationError({
                    'ai_model': 'AI 모델을 선택하세요.',
                })
            attrs['recipe_category'] = None
            if 'workflow_steps' not in attrs:
                attrs.setdefault('workflow_steps', [])
            if 'agent_pattern' not in attrs:
                attrs.setdefault('agent_pattern', '')

        return attrs

    def _resolve_recipe_category(self, name: str):
        slug = slugify(name, allow_unicode=True) or name.lower().replace(' ', '-')
        category, _ = RecipeCategory.objects.get_or_create(
            slug=slug,
            defaults={'name': name},
        )
        return category

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
