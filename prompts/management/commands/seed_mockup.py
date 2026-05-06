from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from interaction.models import Comment, Like
from prompts.models import Category, Prompt, Tag


User = get_user_model()


PROMPT_CONTENT = """당신은 전문 AI 프롬프트 엔지니어입니다.

아래 목적에 맞게 입력값을 분석하고, 실행 가능한 결과물을 구조화해서 작성해주세요.

## 요청
[여기에 사용자의 원본 요청을 입력하세요]

## 출력 형식
1. 핵심 요약
2. 단계별 실행안
3. 바로 사용할 수 있는 최종 결과물
"""


PROMPTS = [
    {
        'title': '블로그 포스트를 SEO 최적화된 글로 변환하는 프롬프트',
        'description': '기존 블로그 글을 입력하면 키워드 분석, 메타 설명, 헤딩 구조까지 자동으로 최적화해주는 고급 프롬프트입니다.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5',
        'is_free': False,
        'price': 3000,
        'tags': ['글쓰기', 'SEO', '마케팅'],
        'author': '김프롬',
        'views': 1420,
        'likes': 128,
        'comments': 24,
    },
    {
        'title': 'Python 코드 리뷰 & 리팩토링 어시스턴트',
        'description': '코드를 붙여넣으면 버그 탐지, 성능 개선, PEP8 스타일 가이드 준수 여부까지 체크해주는 개발자 필수 프롬프트.',
        'category': 'Claude',
        'ai_model': 'claude-sonnet-4-6',
        'is_free': True,
        'price': 0,
        'tags': ['코딩', 'Python', '리뷰'],
        'author': 'devLee',
        'views': 892,
        'likes': 96,
        'comments': 18,
    },
    {
        'title': '사실적인 제품 목업 이미지 생성 프롬프트',
        'description': '제품 설명만 입력하면 다양한 앵글과 배경의 사실적인 목업 이미지를 생성할 수 있는 프롬프트.',
        'category': None,
        'ai_model': 'other',
        'is_free': False,
        'price': 5000,
        'tags': ['이미지', '목업', '디자인'],
        'author': 'artPark',
        'views': 2310,
        'likes': 210,
        'comments': 41,
    },
    {
        'title': '논문 요약 & 핵심 인사이트 추출기',
        'description': '학술 논문을 입력하면 핵심 논지, 방법론, 결과를 구조화된 형태로 정리해주는 연구자용 프롬프트.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5-instant',
        'is_free': True,
        'price': 0,
        'tags': ['요약', '학술', '연구'],
        'author': 'scholar_J',
        'views': 645,
        'likes': 74,
        'comments': 12,
    },
    {
        'title': 'Instagram 릴스 스크립트 자동 생성기',
        'description': '주제와 타겟 오디언스만 입력하면 후크, 본문, CTA까지 포함된 릴스 스크립트를 만들어주는 마케터용 프롬프트.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5',
        'is_free': False,
        'price': 2000,
        'tags': ['마케팅', 'SNS', '콘텐츠'],
        'author': 'mkt_guru',
        'views': 1870,
        'likes': 163,
        'comments': 29,
    },
    {
        'title': '영어 이메일 톤 조절 및 교정 프롬프트',
        'description': '한국어로 의도를 설명하면 Formal, Casual, Friendly 등 원하는 톤의 영어 이메일을 작성해주는 비즈니스 프롬프트.',
        'category': 'Claude',
        'ai_model': 'claude-opus-4-7',
        'is_free': True,
        'price': 0,
        'tags': ['번역', '이메일', '비즈니스'],
        'author': 'biz_writer',
        'views': 734,
        'likes': 89,
        'comments': 15,
    },
    {
        'title': 'Stable Diffusion 캐릭터 콘셉트 프롬프트',
        'description': '캐릭터의 세계관, 의상, 조명, 카메라 구도를 한 번에 정리하는 이미지 생성용 프롬프트.',
        'category': None,
        'ai_model': 'other',
        'is_free': False,
        'price': 4000,
        'tags': ['이미지', '캐릭터', '디자인'],
        'author': 'artPark',
        'views': 980,
        'likes': 112,
        'comments': 20,
    },
    {
        'title': 'Gemini 멀티모달 자료 분석 프롬프트',
        'description': '이미지와 텍스트 자료를 함께 넣고 핵심 패턴, 요약, 실행 과제를 도출하는 분석 프롬프트.',
        'category': 'Gemini',
        'ai_model': 'gemini-3-1-pro',
        'is_free': True,
        'price': 0,
        'tags': ['분석', '요약', '교육'],
        'author': 'scholar_J',
        'views': 512,
        'likes': 68,
        'comments': 9,
    },
]

AUTHOR_EMAILS = {
    '김프롬': 'kim-prom@promptory.local',
    'devLee': 'devlee@promptory.local',
    'artPark': 'artpark@promptory.local',
    'scholar_J': 'scholar-j@promptory.local',
    'mkt_guru': 'mkt-guru@promptory.local',
    'biz_writer': 'biz-writer@promptory.local',
}


COMMENT_SAMPLES = [
    '이 프롬프트 실제로 써봤는데 결과가 꽤 안정적입니다.',
    '팀 내부 문서 작업에 바로 활용하기 좋았어요.',
    '출력 형식이 명확해서 수정하기 편합니다.',
    '예시 입력까지 추가하면 더 좋아질 것 같습니다.',
    '가격이 아깝지 않은 프롬프트입니다.',
]


class Command(BaseCommand):
    help = 'Seed local database with Promptory UI mockup data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete previous mockup seed data before inserting.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            self._reset_seed_data()

        categories = self._create_categories()
        tags = self._create_tags()
        authors = self._create_authors()
        like_users = self._create_like_users(max(item['likes'] for item in PROMPTS))

        created_prompts = []
        for item in PROMPTS:
            prompt, _ = Prompt.all_objects.update_or_create(
                title=item['title'],
                user=authors[item['author']],
                defaults={
                    'category': categories.get(item['category']),
                    'content': PROMPT_CONTENT,
                    'description': item['description'],
                    'ai_model': item['ai_model'],
                    'is_free': item['is_free'],
                    'price': item['price'],
                    'view_count': item['views'],
                    'is_deleted': False,
                    'deleted_at': None,
                    'deleted_by': None,
                },
            )
            prompt.tags.set(tags[name] for name in item['tags'])
            self._sync_likes(prompt, like_users, item['likes'])
            self._sync_comments(prompt, authors, item['comments'])
            created_prompts.append(prompt)

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(categories)} categories, {len(tags)} tags, '
            f'{len(authors)} authors, {len(created_prompts)} prompts.'
        ))

    def _reset_seed_data(self):
        seed_emails = [self._email_for_author(item['author']) for item in PROMPTS]
        seed_emails += [f'mock-like-{index:03d}@promptory.local' for index in range(1, 211)]
        Prompt.all_objects.filter(title__in=[item['title'] for item in PROMPTS]).delete()
        User.objects.filter(email__in=seed_emails).delete()

    def _create_categories(self):
        Category.objects.filter(slug__in=['midjourney', 'stable-diffusion']).delete()
        category_names = ['ChatGPT', 'Claude', 'Gemini']
        categories = {}
        for name in category_names:
            category, _ = Category.objects.update_or_create(
                slug=slugify(name),
                defaults={'name': name, 'description': f'{name} 프롬프트 모음'},
            )
            categories[name] = category
        return categories

    def _create_tags(self):
        tag_names = sorted({tag for item in PROMPTS for tag in item['tags']} | {
            '글쓰기', '코딩', '마케팅', '번역', '이미지', '분석', '요약', '교육',
        })
        tags = {}
        for name in tag_names:
            tag, _ = Tag.objects.update_or_create(
                slug=slugify(name, allow_unicode=True),
                defaults={'name': name},
            )
            tags[name] = tag
        return tags

    def _create_authors(self):
        authors = {}
        for name in sorted({item['author'] for item in PROMPTS}):
            user, _ = User.objects.update_or_create(
                email=self._email_for_author(name),
                defaults={
                    'username': name,
                    'bio': 'Promptory 목업 시드 작성자입니다.',
                    'is_active': True,
                },
            )
            user.set_password('Promptory123!')
            user.save(update_fields=['password'])
            authors[name] = user
        return authors

    def _create_like_users(self, count):
        users = []
        for index in range(1, count + 1):
            user, _ = User.objects.update_or_create(
                email=f'mock-like-{index:03d}@promptory.local',
                defaults={'username': f'mock_like_{index:03d}', 'is_active': True},
            )
            users.append(user)
        return users

    def _sync_likes(self, prompt, users, count):
        Like.objects.filter(prompt=prompt).delete()
        Like.objects.bulk_create([
            Like(prompt=prompt, user=user) for user in users[:count]
        ], ignore_conflicts=True)

    def _sync_comments(self, prompt, authors, count):
        Comment.all_objects.filter(prompt=prompt).delete()
        author_list = list(authors.values())
        comments = []
        for index in range(count):
            user = author_list[index % len(author_list)]
            sample = COMMENT_SAMPLES[index % len(COMMENT_SAMPLES)]
            comments.append(Comment(
                prompt=prompt,
                user=user,
                content=f'{sample} ({index + 1})',
            ))
        Comment.objects.bulk_create(comments)

    def _email_for_author(self, name):
        return AUTHOR_EMAILS[name]
