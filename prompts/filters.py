import django_filters
from .models import Prompt


class PromptFilter(django_filters.FilterSet):
    """
    검색 파라미터:
    ?search=키워드       title 포함 검색
    ?category=1          카테고리 ID
    ?ai_model=gpt-5-5    AI 모델
    ?is_free=true        무료 여부
    ?tag=python          태그 슬러그
    ?ordering=-created_at  정렬 (최신순 기본)
    """
    tag = django_filters.CharFilter(field_name='tags__slug', lookup_expr='exact')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Prompt
        fields = {
            'category': ['exact'],
            'ai_model': ['exact'],
            'is_free': ['exact'],
        }
