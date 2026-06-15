from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from prompts.models import Prompt, RecipeCategory
from .models import BlueprintDesign
from .serializers import (
    BlueprintDesignCreateSerializer,
    BlueprintDesignSerializer,
    BlueprintPublishRecipeSerializer,
)
from .services.blueprint import (
    compose_design_content,
    pattern_from_transformation,
    steps_to_workflow,
    sync_design_from_task,
)


def _design_title(title: str, brief: str) -> str:
    cleaned = (title or '').strip()
    if cleaned:
        return cleaned[:200]
    return (brief or '').strip()[:80] or '새 설계서'


class BlueprintDesignListCreateView(APIView):
    """GET/POST /api/blueprints/design/ — 내 설계 목록 · 새 설계 시작."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        designs = BlueprintDesign.objects.filter(user=request.user).select_related(
            'transformation', 'recipe',
        )
        synced = [sync_design_from_task(d) for d in designs]
        return Response(BlueprintDesignSerializer(synced, many=True).data)

    def post(self, request):
        serializer = BlueprintDesignCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        title = _design_title(data.get('title', ''), data['brief'])
        content = compose_design_content(data['brief'], data.get('extra_context', ''))

        source_prompt = Prompt.objects.create(
            user=request.user,
            title=f'[설계 초안] {title}',
            content=content,
            description='설계서 만들기 도구에서 생성된 내부 초안입니다.',
            prompt_type='single_prompt',
            is_blueprint_draft=True,
        )
        design = BlueprintDesign.objects.create(
            user=request.user,
            title=title,
            brief=data['brief'],
            extra_context=data.get('extra_context', ''),
            status='pending',
            source_prompt=source_prompt,
        )

        return Response({
            'id': design.id,
            'prompt_id': source_prompt.id,
            'status': 'pending',
            'design_url': f'/api/blueprints/design/{design.id}/',
            'transform_url': f'/api/prompts/{source_prompt.id}/transform/',
        }, status=status.HTTP_201_CREATED)


class BlueprintDesignDetailView(APIView):
    """GET/DELETE /api/blueprints/design/<id>/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        design = get_object_or_404(
            BlueprintDesign.objects.select_related('transformation', 'recipe'),
            pk=pk,
            user=request.user,
        )
        design = sync_design_from_task(design)
        return Response(BlueprintDesignSerializer(design).data)

    def delete(self, request, pk):
        design = get_object_or_404(
            BlueprintDesign.objects.select_related('recipe'),
            pk=pk,
            user=request.user,
        )
        recipe_id = design.recipe_id
        if design.recipe and not design.recipe.is_deleted:
            design.recipe.soft_delete(user=request.user)
        design.delete()
        payload = {'detail': '설계서가 삭제되었습니다.'}
        if recipe_id:
            payload['recipe_id'] = recipe_id
        return Response(payload, status=status.HTTP_200_OK)


class BlueprintPublishRecipeView(APIView):
    """POST /api/blueprints/design/<id>/publish-recipe/ — 설계 결과를 에이전트 레시피 초안으로 등록."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        design = get_object_or_404(
            BlueprintDesign.objects.select_related('transformation'),
            pk=pk,
            user=request.user,
        )
        if design.status != 'success' or not design.transformation_id:
            return Response(
                {'detail': '설계가 완료된 후에 레시피로 등록할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if design.recipe_id:
            return Response({
                'detail': '이미 레시피로 등록되었습니다.',
                'recipe_id': design.recipe_id,
                'recipe_url': f'/prompts/{design.recipe_id}/',
            }, status=status.HTTP_200_OK)

        body = BlueprintPublishRecipeSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        payload = body.validated_data
        transformation = design.transformation

        recipe_title = (payload.get('title') or design.title or design.brief[:80])[:200]
        description = payload.get('description') or design.brief
        recipe_category = None
        category_name = (payload.get('recipe_category_name') or '').strip()
        if category_name:
            base_slug = slugify(category_name, allow_unicode=True) or 'recipe'
            slug = base_slug
            suffix = 1
            while RecipeCategory.objects.filter(slug=slug).exclude(name=category_name).exists():
                slug = f'{base_slug}-{suffix}'
                suffix += 1
            recipe_category, _ = RecipeCategory.objects.get_or_create(
                name=category_name,
                defaults={'slug': slug},
            )

        recipe = Prompt.objects.create(
            user=request.user,
            title=recipe_title,
            description=description[:5000] if description else '',
            content=design.brief,
            prompt_type='agent_recipe',
            agent_pattern=pattern_from_transformation(transformation.overall_pattern),
            workflow_steps=steps_to_workflow(transformation.decomposed_steps),
            recipe_category=recipe_category,
        )
        design.recipe = recipe
        design.save(update_fields=['recipe', 'updated_at'])

        return Response({
            'recipe_id': recipe.id,
            'recipe_url': f'/prompts/{recipe.id}/',
            'edit_url': f'/prompts/{recipe.id}/edit/',
        }, status=status.HTTP_201_CREATED)
