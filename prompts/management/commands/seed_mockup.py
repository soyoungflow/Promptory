from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from interaction.models import Comment, Like
from prompts.models import Category, RecipeCategory, Prompt, Tag


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

AGENT_RECIPE_CONTENT = """블로그 글쓰기 에이전트 워크플로우

이 프롬프트는 단일 명령으로 4단계 에이전트 체인을 실행합니다.
1단계 리서치 → 2단계 개요 → 3단계 초안 → 4단계 검토
"""

AGENT_RECIPE_WORKFLOW = [
    {
        "step": 1, "name": "리서치",
        "system_message": "주제에 관련된 최신 정보 5개 수집",
        "tool": "web_search",
        "context_policy": {
            "previous_output_strategy": "none",
            "memory_scope": "this_step_only",
            "reason": "첫 단계는 원본 프롬프트만",
        },
        "harness_policy": {
            "timeout_seconds": 45, "max_retries": 3,
            "fallback_action": "use_default", "cost_budget_tokens": 3000,
        },
        "knowledge_refs": [
            {"type": "api", "source": "네이버 블로그 검색 API", "usage": "always", "description": "국내 최신 트렌드 확보"},
        ],
        "verification_criteria": {
            "success_signals": ["URL 5개 이상", "발행일 1년 이내"],
            "failure_signals": ["검색 결과 0건"],
            "evaluator": "rule", "min_quality_score": 0.7, "on_fail": "retry",
        },
    },
    {
        "step": 2, "name": "개요",
        "system_message": "수집한 정보를 H2/H3 헤딩으로 구조화",
        "tool": "outline_generator",
        "context_policy": {
            "previous_output_strategy": "summarize_500",
            "memory_scope": "all_previous",
            "reason": "리서치 결과 누적 시 컨텍스트 폭발 — 요약 필수",
        },
        "harness_policy": {
            "timeout_seconds": 20, "max_retries": 2,
            "validation_schema": "outline_v1.json", "cost_budget_tokens": 1500,
        },
        "knowledge_refs": [
            {"type": "document", "source": "SEO 키워드 베스트프랙티스", "usage": "always", "description": "SEO 친화적 헤딩 구조"},
        ],
        "verification_criteria": {
            "success_signals": ["H2 3개 이상", "각 H2 아래 H3 2개 이상"],
            "failure_signals": ["헤딩 없음"],
            "evaluator": "rule", "min_quality_score": 0.75, "on_fail": "retry",
        },
    },
    {
        "step": 3, "name": "초안",
        "system_message": "섹션당 300자 이상 풀어쓰기",
        "tool": "text_generation",
        "context_policy": {
            "previous_output_strategy": "full",
            "memory_scope": "all_previous",
            "reason": "개요는 짧고 초안 생성에 필수",
        },
        "harness_policy": {
            "timeout_seconds": 60, "max_retries": 2, "cost_budget_tokens": 4000,
        },
        "knowledge_refs": [
            {"type": "document", "source": "브랜드 톤매뉴얼.pdf", "usage": "always", "description": "일관된 브랜드 보이스 유지"},
        ],
        "verification_criteria": {
            "success_signals": ["섹션당 300자 이상", "브랜드 톤 일치"],
            "failure_signals": ["TODO 포함", "반복 문장"],
            "evaluator": "llm_judge", "min_quality_score": 0.7, "on_fail": "retry",
        },
    },
    {
        "step": 4, "name": "검토",
        "system_message": "문법/사실/일관성 점검 및 수정 제안",
        "tool": "reflection",
        "context_policy": {
            "previous_output_strategy": "selective",
            "memory_scope": "all_previous",
            "reason": "초안 중심 검토, 리서치는 사실 검증용만",
        },
        "harness_policy": {
            "timeout_seconds": 30, "max_retries": 1,
            "fallback_action": "skip_step", "cost_budget_tokens": 2000,
        },
        "knowledge_refs": [
            {"type": "api", "source": "맞춤법 검사 API", "usage": "always", "description": "문법 오류 자동 검출"},
        ],
        "verification_criteria": {
            "success_signals": ["수정 제안 1개 이상", "문법 오류 0건"],
            "failure_signals": ["근거 없는 제안"],
            "evaluator": "llm_judge", "min_quality_score": 0.8, "on_fail": "escalate",
        },
    },
]


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

# 추가 시드(20개): 직무별 실사용 시나리오 중심 데이터
EXTRA_PROMPTS = [
    {
        'title': '신규 SaaS 온보딩 메일 5종 자동 작성 템플릿',
        'description': '가입 직후부터 7일차까지 발송할 온보딩 이메일 시퀀스를 서비스 특성에 맞게 생성합니다.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5',
        'is_free': False,
        'price': 2500,
        'tags': ['마케팅', '이메일', '글쓰기'],
        'author': 'mkt_guru',
        'views': 1335,
        'likes': 141,
        'comments': 19,
    },
    {
        'title': '고객 인터뷰 녹취록에서 VOC 이슈 분류하기',
        'description': '긴 인터뷰 텍스트를 기능요구/버그/요금제/UX 이슈로 분류하고 우선순위를 제안합니다.',
        'category': 'Claude',
        'ai_model': 'claude-opus-4-7',
        'is_free': True,
        'price': 0,
        'tags': ['분석', '요약', '비즈니스'],
        'author': 'scholar_J',
        'views': 989,
        'likes': 112,
        'comments': 14,
    },
    {
        'title': '주간 스프린트 회고 액션아이템 생성기',
        'description': '회고 메모를 입력하면 팀별 액션아이템, 담당자, 완료기한 초안을 자동으로 작성합니다.',
        'category': 'Gemini',
        'ai_model': 'gemini-3-1-pro',
        'is_free': True,
        'price': 0,
        'tags': ['요약', '교육', '비즈니스'],
        'author': 'devLee',
        'views': 842,
        'likes': 95,
        'comments': 11,
    },
    {
        'title': '이커머스 상품 상세페이지 카피 개선 프롬프트',
        'description': '기존 상세페이지 문구를 전환 중심 구조(문제-해결-근거-CTA)로 재작성합니다.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5-instant',
        'is_free': False,
        'price': 1800,
        'tags': ['마케팅', '글쓰기', '콘텐츠'],
        'author': '김프롬',
        'views': 1208,
        'likes': 134,
        'comments': 17,
    },
    {
        'title': '장애 보고서 기반 RCA(근본 원인 분석) 정리',
        'description': '운영 장애 로그와 타임라인을 넣으면 원인-영향-재발방지안을 표준 포맷으로 작성합니다.',
        'category': 'Claude',
        'ai_model': 'claude-sonnet-4-6',
        'is_free': False,
        'price': 3200,
        'tags': ['분석', '리뷰', '비즈니스'],
        'author': 'devLee',
        'views': 1113,
        'likes': 126,
        'comments': 18,
    },
    {
        'title': 'SQL 쿼리 성능 개선 리뷰 체크리스트 생성',
        'description': '실행계획과 쿼리를 기반으로 인덱스/조인/필터링 최적화 포인트를 정리합니다.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5',
        'is_free': False,
        'price': 2900,
        'tags': ['코딩', 'Python', '리뷰'],
        'author': 'devLee',
        'views': 1047,
        'likes': 119,
        'comments': 15,
    },
    {
        'title': 'B2B 제안서 Executive Summary 작성기',
        'description': '요구사항 문서를 요약해 의사결정자용 1페이지 제안 요약을 만듭니다.',
        'category': 'Claude',
        'ai_model': 'claude-opus-4-7',
        'is_free': True,
        'price': 0,
        'tags': ['글쓰기', '비즈니스', '요약'],
        'author': 'biz_writer',
        'views': 915,
        'likes': 101,
        'comments': 13,
    },
    {
        'title': '채용 공고(JD) 편향 표현 점검 프롬프트',
        'description': '채용 공고 문구에서 과도한 조건, 차별 소지가 있는 표현을 찾아 대체 문안을 제안합니다.',
        'category': 'Gemini',
        'ai_model': 'gemini-3-0-flash',
        'is_free': True,
        'price': 0,
        'tags': ['HR', '글쓰기', '리뷰'],
        'author': 'biz_writer',
        'views': 768,
        'likes': 87,
        'comments': 10,
    },
    {
        'title': '경쟁사 랜딩페이지 벤치마크 분석 템플릿',
        'description': '경쟁사 랜딩페이지 텍스트를 비교해 메시지 포지셔닝과 CTA 차이를 정리합니다.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5-instant',
        'is_free': False,
        'price': 2100,
        'tags': ['마케팅', '분석', '콘텐츠'],
        'author': 'mkt_guru',
        'views': 1098,
        'likes': 123,
        'comments': 16,
    },
    {
        'title': '고객 CS 답변 매크로 개선(공감형 톤)',
        'description': '클레임/환불/배송문의 유형별로 공감 문장과 해결 안내를 포함한 답변 템플릿을 만듭니다.',
        'category': 'Claude',
        'ai_model': 'claude-sonnet-4-6',
        'is_free': True,
        'price': 0,
        'tags': ['이메일', '비즈니스', '글쓰기'],
        'author': 'biz_writer',
        'views': 884,
        'likes': 98,
        'comments': 12,
    },
    {
        'title': '분기 KPI 리포트 자동 해설 작성',
        'description': '핵심 지표 테이블을 넣으면 증감 원인, 위험요인, 다음 액션을 경영진 보고 형식으로 생성합니다.',
        'category': 'Gemini',
        'ai_model': 'gemini-3-1-pro',
        'is_free': False,
        'price': 2700,
        'tags': ['분석', '요약', '비즈니스'],
        'author': 'scholar_J',
        'views': 972,
        'likes': 108,
        'comments': 13,
    },
    {
        'title': 'API 명세서 기반 테스트 케이스 초안 생성',
        'description': '엔드포인트 명세를 입력하면 정상/예외/권한 테스트 케이스를 표 형태로 생성합니다.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5',
        'is_free': False,
        'price': 3000,
        'tags': ['코딩', '리뷰', '분석'],
        'author': 'devLee',
        'views': 1186,
        'likes': 132,
        'comments': 18,
    },
    {
        'title': '회의록에서 의사결정 로그만 추출하기',
        'description': '긴 회의록에서 결정사항/미결사항/담당자/마감일을 자동 추출합니다.',
        'category': 'Claude',
        'ai_model': 'claude-opus-4-7',
        'is_free': True,
        'price': 0,
        'tags': ['요약', '비즈니스', '교육'],
        'author': '김프롬',
        'views': 903,
        'likes': 99,
        'comments': 11,
    },
    {
        'title': '신입 온보딩 학습자료 주차별 커리큘럼 설계',
        'description': '직무 설명을 바탕으로 4주 온보딩 커리큘럼과 실습 과제를 구성합니다.',
        'category': 'Gemini',
        'ai_model': 'gemini-3-0-flash',
        'is_free': False,
        'price': 1600,
        'tags': ['교육', '요약', '글쓰기'],
        'author': 'scholar_J',
        'views': 746,
        'likes': 82,
        'comments': 9,
    },
    {
        'title': '프로덕트 릴리즈 노트 초안 자동 생성',
        'description': '깃 커밋/이슈 내역을 입력하면 사용자 관점 릴리즈 노트를 버전별로 작성합니다.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5-instant',
        'is_free': True,
        'price': 0,
        'tags': ['글쓰기', '코딩', '비즈니스'],
        'author': '김프롬',
        'views': 1011,
        'likes': 113,
        'comments': 14,
    },
    {
        'title': '광고 성과 부진 캠페인 디버깅 프롬프트',
        'description': '소재/타겟/예산 데이터를 기반으로 성과 저하 원인을 가설 트리로 정리합니다.',
        'category': 'Claude',
        'ai_model': 'claude-sonnet-4-6',
        'is_free': False,
        'price': 2400,
        'tags': ['마케팅', '분석', '리뷰'],
        'author': 'mkt_guru',
        'views': 1073,
        'likes': 121,
        'comments': 15,
    },
    {
        'title': '사내 문서 한영 번역 + 용어집 일관화',
        'description': '기존 용어집을 기준으로 문서 번역 결과의 표현 일관성을 유지합니다.',
        'category': 'Gemini',
        'ai_model': 'gemini-3-1-pro',
        'is_free': True,
        'price': 0,
        'tags': ['번역', '글쓰기', '비즈니스'],
        'author': 'biz_writer',
        'views': 838,
        'likes': 93,
        'comments': 10,
    },
    {
        'title': 'UI 카피 A/B 테스트 가설 작성 도우미',
        'description': '현재 카피와 목표 지표를 넣으면 실험 가설, 성공 기준, 샘플 수 추정 기준을 제시합니다.',
        'category': 'ChatGPT',
        'ai_model': 'gpt-5-5',
        'is_free': False,
        'price': 2200,
        'tags': ['마케팅', '분석', '글쓰기'],
        'author': 'mkt_guru',
        'views': 954,
        'likes': 106,
        'comments': 12,
    },
    {
        'title': '데이터 분석 결과를 임원 보고용 스토리로 변환',
        'description': '분석 지표/차트를 입력하면 문제정의-인사이트-의사결정 포인트 순서로 재구성합니다.',
        'category': 'Claude',
        'ai_model': 'claude-opus-4-7',
        'is_free': False,
        'price': 3100,
        'tags': ['분석', '요약', '글쓰기'],
        'author': 'scholar_J',
        'views': 1142,
        'likes': 129,
        'comments': 17,
    },
    {
        'title': '기술 블로그 초안에서 코드 예제 개선하기',
        'description': '초안 글의 코드 블록을 실행 가능한 형태로 보정하고 설명 흐름을 개선합니다.',
        'category': 'Gemini',
        'ai_model': 'gemini-3-0-flash',
        'is_free': True,
        'price': 0,
        'tags': ['코딩', '글쓰기', '리뷰'],
        'author': 'devLee',
        'views': 821,
        'likes': 89,
        'comments': 10,
    },
]

AGENT_RECIPE_PROMPTS = [
    {
        'title': '블로그 글쓰기 에이전트 (4단계 자동 분해)',
        'description': '리서치-개요-초안-검토를 자동으로 실행하는 에이전트 레시피 템플릿.',
        'recipe_category': '글쓰기',
        'is_free': True,
        'price': 0,
        'tags': ['글쓰기', '에이전트', '자동화'],
        'author': '김프롬',
        'views': 320,
        'likes': 41,
        'comments': 7,
        'prompt_type': 'agent_recipe',
        'workflow_steps': AGENT_RECIPE_WORKFLOW,
        'agent_pattern': 'sequential',
        'content_override': AGENT_RECIPE_CONTENT,
    },
    {
        'title': '회의록 요약 에이전트 (의사결정 추출)',
        'description': '회의 텍스트에서 의사결정·담당자·기한을 단계적으로 추출하는 레시피.',
        'recipe_category': '비즈니스',
        'is_free': True,
        'price': 0,
        'tags': ['요약', '비즈니스', '에이전트'],
        'author': 'devLee',
        'views': 280,
        'likes': 36,
        'comments': 5,
        'prompt_type': 'agent_recipe',
        'workflow_steps': AGENT_RECIPE_WORKFLOW,
        'agent_pattern': 'sequential',
        'content_override': AGENT_RECIPE_CONTENT,
    },
    {
        'title': '코드 리뷰 에이전트 (분석-수정안-검증)',
        'description': '코드 품질 문제를 찾아 수정안과 검증 체크리스트를 생성하는 레시피.',
        'recipe_category': '코딩',
        'is_free': False,
        'price': 1500,
        'tags': ['코딩', '리뷰', '에이전트'],
        'author': 'devLee',
        'views': 260,
        'likes': 33,
        'comments': 4,
        'prompt_type': 'agent_recipe',
        'workflow_steps': AGENT_RECIPE_WORKFLOW,
        'agent_pattern': 'sequential',
        'content_override': AGENT_RECIPE_CONTENT,
    },
]

PROMPTS.extend(EXTRA_PROMPTS)
PROMPTS.extend(AGENT_RECIPE_PROMPTS)

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

        recipe_categories = self._create_recipe_categories()

        created_prompts = []
        for item in PROMPTS:
            is_recipe = item.get('prompt_type') == 'agent_recipe'
            prompt, _ = Prompt.all_objects.update_or_create(
                title=item['title'],
                user=authors[item['author']],
                defaults={
                    'category': None if is_recipe else categories.get(item['category']),
                    'recipe_category': (
                        recipe_categories.get(item['recipe_category']) if is_recipe else None
                    ),
                    'content': item.get('content_override', PROMPT_CONTENT),
                    'description': item['description'],
                    'ai_model': 'other' if is_recipe else item['ai_model'],
                    'prompt_type': item.get('prompt_type', 'single_prompt'),
                    'workflow_steps': item.get('workflow_steps', []),
                    'agent_pattern': item.get('agent_pattern', ''),
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

    def _create_recipe_categories(self):
        names = sorted({
            item['recipe_category']
            for item in PROMPTS
            if item.get('prompt_type') == 'agent_recipe' and item.get('recipe_category')
        })
        recipe_categories = {}
        for name in names:
            category, _ = RecipeCategory.objects.update_or_create(
                slug=slugify(name, allow_unicode=True),
                defaults={'name': name},
            )
            recipe_categories[name] = category
        return recipe_categories

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
