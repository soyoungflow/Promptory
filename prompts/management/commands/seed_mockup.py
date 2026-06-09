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

# 에이전트 레시피 추가 시드 — 유형·단계·도구가 서로 다른 실무 시나리오
AGENT_RECIPE_EXTRA = [
    {
        'title': '월요일 아침 마케팅 리포트 봇',
        'description': 'GA4·Meta 광고·Search Console 수치를 모아 팀 슬랙 채널용 주간 요약을 만듭니다. 지난주 대비 증감과 이상 징후만 짚어 줍니다.',
        'recipe_category': '마케팅',
        'is_free': True,
        'price': 0,
        'tags': ['마케팅', '분석', '자동화'],
        'author': 'mkt_guru',
        'views': 487,
        'likes': 52,
        'comments': 6,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'sequential',
        'content_override': '매주 월요일 09:00에 전주(월~일) 마케팅 지표를 수집·해석해 #growth 채널에 올릴 요약 리포트를 생성합니다.',
        'workflow_steps': [
            {
                'step': 1, 'name': '지표 수집',
                'system_message': 'GA4 전환·세션, Meta Ads ROAS·CPA, Search Console 클릭·노출을 동일 기간으로 조회해 표로 정리',
                'tool': 'ga4_api',
            },
            {
                'step': 2, 'name': '전주 대비 해석',
                'system_message': '지표별 WoW 증감률을 계산하고 20% 이상 변동 항목에 원인 가설 1개씩 붙여라',
                'tool': 'spreadsheet',
            },
            {
                'step': 3, 'name': '슬랙 메시지 작성',
                'system_message': '이모지 과다 사용 없이 15줄 이내 bullet로 요약. 액션 아이템은 담당자 태그 없이 제안만',
                'tool': 'slack_post',
            },
        ],
    },
    {
        'title': 'CS 문의 자동 분류 + 1차 답변 초안',
        'description': 'Zendesk 티켓을 환불·배송·결제·기능문의로 나누고, 정책 문서를 참고한 1차 답변 초안을 작성합니다.',
        'recipe_category': '고객지원',
        'is_free': True,
        'price': 0,
        'tags': ['비즈니스', '이메일', '자동화'],
        'author': 'biz_writer',
        'views': 612,
        'likes': 67,
        'comments': 8,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'react',
        'content_override': '신규 CS 티켓이 들어오면 유형 분류 → 관련 FAQ 검색 → 공감형 톤의 답변 초안까지 한 번에 처리합니다.',
        'workflow_steps': [
            {
                'step': 1, 'name': '티켓 분류',
                'system_message': '제목·본문을 읽고 refund/shipping/billing/feature/other 중 하나로 라벨링. confidence 0.7 미만이면 other',
                'tool': 'ticket_classifier',
            },
            {
                'step': 2, 'name': '정책 검색',
                'system_message': '분류 결과에 맞는 사내 환불·배송 정책 조항을 RAG에서 찾아 인용 문장 추출',
                'tool': 'rag_search',
            },
            {
                'step': 3, 'name': '답변 초안',
                'system_message': '고객 이름 호칭, 사과 1문장, 해결 절차 3단계, 추가 문의 안내 순으로 200자 내외 한국어 작성',
                'tool': 'text_generation',
            },
        ],
    },
    {
        'title': '경쟁 쇼핑몰 가격·프로모션 모니터',
        'description': '지정 URL 5곳의 대표 SKU 가격과 배너 프로모션 문구를 스크랩해 비교표로 정리합니다.',
        'recipe_category': '이커머스',
        'is_free': False,
        'price': 2200,
        'tags': ['분석', '마케팅', '자동화'],
        'author': 'mkt_guru',
        'views': 398,
        'likes': 44,
        'comments': 5,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'sequential',
        'content_override': '자사 대표 상품 3개 SKU에 대해 경쟁사 5곳의 판매가·할인율·무료배송 조건을 매일 오전 비교합니다.',
        'workflow_steps': [
            {
                'step': 1, 'name': '페이지 스크랩',
                'system_message': 'URL 목록에서 상품명·판매가·할인 전 가격·배송비 텍스트 추출. CAPTCHA 시 스킵하고 로그 남김',
                'tool': 'web_scraper',
            },
            {
                'step': 2, 'name': '정규화',
                'system_message': '통화·단위 통일, 동일 용량/옵션끼리만 비교 가능하도록 SKU 매핑 테이블 적용',
                'tool': 'data_normalizer',
            },
            {
                'step': 3, 'name': '인사이트 한 줄',
                'system_message': '자사 대비 최저가·최고 할인율 경쟁사와 가격 차이(원·%)를 bullet 3개로 요약',
                'tool': 'text_generation',
            },
        ],
    },
    {
        'title': 'PRD 초안 멀티 에이전트 (PM·디자인·엔지니어)',
        'description': '기능 아이디어 한 줄을 넣으면 PM·디자이너·백엔드 관점의 요구사항 초안을 병렬 작성 후 통합합니다.',
        'recipe_category': '프로덕트',
        'is_free': False,
        'price': 3500,
        'tags': ['비즈니스', '글쓰기', '에이전트'],
        'author': 'scholar_J',
        'views': 541,
        'likes': 58,
        'comments': 9,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'multi_agent',
        'content_override': '신규 기능「알림 센터」같은 한 줄 입력 → 역할별 에이전트가 각자 섹션 작성 → PM 에이전트가 충돌 조율.',
        'workflow_steps': [
            {
                'step': 1, 'name': 'PM 에이전트',
                'system_message': '문제정의, 성공 지표, 범위(In/Out), 릴리즈 마일스톤을 PRD 형식으로 작성',
                'tool': 'pm_agent',
            },
            {
                'step': 2, 'name': 'UX 에이전트',
                'system_message': '핵심 사용자 플로우 3개, 빈 상태·에러 상태 UI 요구사항만 bullet로',
                'tool': 'ux_agent',
            },
            {
                'step': 3, 'name': '엔지니어 에이전트',
                'system_message': 'API 엔드포인트 초안, 데이터 모델 필드, 비기능(성능·보안) 요구 5줄 이내',
                'tool': 'eng_agent',
            },
            {
                'step': 4, 'name': '통합·충돌 해소',
                'system_message': '세 에이전트 출력의 모순 제거 후 단일 PRD 목차로 병합. 미결 질문은 Open Questions에',
                'tool': 'orchestrator',
            },
        ],
    },
    {
        'title': '법인카드 영수증 → 지출 분개 초안',
        'description': '영수증 이미지·PDF에서 금액·가맹점·날짜를 읽어 회계 계정과목 후보를 제안합니다.',
        'recipe_category': '재무',
        'is_free': False,
        'price': 2800,
        'tags': ['분석', '비즈니스', '자동화'],
        'author': 'biz_writer',
        'views': 276,
        'likes': 31,
        'comments': 4,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'sequential',
        'content_override': '팀원이 올린 영수증을 OCR → 사내 계정과목 매핑 규칙 적용 → 회계 시스템 업로드용 CSV 행 생성.',
        'workflow_steps': [
            {
                'step': 1, 'name': 'OCR 추출',
                'system_message': '이미지/PDF에서 거래일시, 가맹점명, 공급가액, 부가세, 합계 추출. 불명확 필드는 [확인필요] 태그',
                'tool': 'ocr',
            },
            {
                'step': 2, 'name': '계정과목 매핑',
                'system_message': '가맹점 키워드·금액 구간으로 복리후생비/여비교통비/소모품비 등 후보 2개와 confidence 제시',
                'tool': 'account_mapper',
            },
            {
                'step': 3, 'name': '분개 행 생성',
                'system_message': '차변·대변·적요·증빙번호 형식의 CSV 한 줄 출력. 세금계산서 여부 플래그 포함',
                'tool': 'csv_export',
            },
        ],
    },
    {
        'title': '장기 SEO 콘텐츠 허브 기획 파이프라인',
        'description': '타깃 키워드 클러스터를 잡고 허브·스포크 글 목록과 내부링크 구조를 설계합니다.',
        'recipe_category': '콘텐츠',
        'is_free': True,
        'price': 0,
        'tags': ['SEO', '글쓰기', '마케팅'],
        'author': '김프롬',
        'views': 723,
        'likes': 81,
        'comments': 11,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'sequential',
        'content_override': '「B2B SaaS 온보딩」같은 시드 키워드로 3개월치 허브 페이지 + 서브 포스트 12편 주제를 설계합니다.',
        'workflow_steps': [
            {
                'step': 1, 'name': '키워드 클러스터',
                'system_message': '시드 키워드 기준 검색량·난이도 추정 후 pillar 1개 + cluster 8~12개 제안',
                'tool': 'keyword_research',
            },
            {
                'step': 2, 'name': '콘텐츠 맵',
                'system_message': '각 글의 검색 의도, H1 후보, 내부링크 대상을 표로 정리',
                'tool': 'outline_generator',
            },
            {
                'step': 3, 'name': '우선순위',
                'system_message': '트래픽 잠재력×제작 난이도 매트릭스로 1주차 착수 3편 선정',
                'tool': 'scoring',
            },
        ],
    },
    {
        'title': '배포 전 릴리즈 게이트 체크',
        'description': 'CHANGELOG·마이그레이션·환경변수 diff를 읽고 배포 리스크와 롤백 포인트를 점검합니다.',
        'recipe_category': '개발',
        'is_free': True,
        'price': 0,
        'tags': ['코딩', '리뷰', '자동화'],
        'author': 'devLee',
        'views': 834,
        'likes': 91,
        'comments': 12,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'reflection',
        'content_override': 'main 브랜치 배포 직전에 변경 파일·DB 마이그레이션·feature flag 목록을 입력하면 Go/No-Go 체크리스트를 만듭니다.',
        'workflow_steps': [
            {
                'step': 1, 'name': '변경 분석',
                'system_message': 'PR 목록에서 breaking change, DB migration, env 추가 여부를 분류',
                'tool': 'git_diff',
            },
            {
                'step': 2, 'name': '리스크 평가',
                'system_message': '영향 범위(유저/매출/데이터)별 High/Med/Low와 완화 방안 1줄씩',
                'tool': 'risk_analyzer',
            },
            {
                'step': 3, 'name': '자기 검토',
                'system_message': '누락된 체크 항목이 없는지 이전 단계 출력을 비판적으로 재검토 후 최종 Go/No-Go',
                'tool': 'reflection',
            },
        ],
    },
    {
        'title': '신규 가입자 7일 온보딩 메일 시퀀스',
        'description': '서비스 소개·핵심 기능·사례·전환 유도까지 5통 메일 초안을 Day별로 작성합니다.',
        'recipe_category': '마케팅',
        'is_free': False,
        'price': 1900,
        'tags': ['이메일', '마케팅', '글쓰기'],
        'author': 'mkt_guru',
        'views': 445,
        'likes': 49,
        'comments': 6,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'sequential',
        'content_override': 'SaaS 무료 체험 가입 후 D+0,1,3,5,7에 발송할 온보딩 메일 제목·프리헤더·본문 초안.',
        'workflow_steps': [
            {
                'step': 1, 'name': '페르소나 정리',
                'system_message': 'ICP 1명의 직무·페인·목표를 5 bullet로 고정 (이후 메일 톤 기준)',
                'tool': 'persona',
            },
            {
                'step': 2, 'name': '시퀀스 설계',
                'system_message': '각 발송일의 목적(활성화/교육/사회적증거/전환)과 CTA 1개씩 매핑',
                'tool': 'sequence_planner',
            },
            {
                'step': 3, 'name': '메일 초안',
                'system_message': '제목 2안, 프리헤더, 본문 150~200자, CTA 버튼 문구까지 5통 작성',
                'tool': 'email_writer',
            },
        ],
    },
    {
        'title': '회의 녹취 → Notion 액션 아이템',
        'description': 'Zoom/Voice 녹취 텍스트에서 결정·미결·담당·기한을 뽑아 Notion DB 형식으로 정리합니다.',
        'recipe_category': '업무자동화',
        'is_free': True,
        'price': 0,
        'tags': ['요약', '비즈니스', '자동화'],
        'author': '김프롬',
        'views': 567,
        'likes': 63,
        'comments': 7,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'sequential',
        'content_override': '주간 스탠드업·기획 회의 녹취를 넣으면 Notion「팀 태스크」DB에 붙여넣을 수 있는 표로 변환.',
        'workflow_steps': [
            {
                'step': 1, 'name': '발화 정리',
                'system_message': '화자 구분이 없으면 추정 태그[발화자A] 부여. 잡담·반복 제거',
                'tool': 'transcript_cleaner',
            },
            {
                'step': 2, 'name': '결정·액션 추출',
                'system_message': 'Decision / Action / Parking Lot 세 컬럼으로 분류. Action은 담당·기한 있으면 함께',
                'tool': 'extractor',
            },
            {
                'step': 3, 'name': 'Notion 포맷',
                'system_message': '태스크명, 상태(할일), 담당, 마감일, 회의 링크 컬럼을 가진 markdown 테이블 출력',
                'tool': 'notion_export',
            },
        ],
    },
    {
        'title': '인스타·링크드인 주간 콘텐츠 캘린더',
        'description': '한 주치 SNS 포스트 주제·훅·해시태그·게시 요일을 플랫폼별로 제안합니다.',
        'recipe_category': 'SNS',
        'is_free': False,
        'price': 1600,
        'tags': ['SNS', '콘텐츠', '마케팅'],
        'author': 'artPark',
        'views': 512,
        'likes': 56,
        'comments': 8,
        'prompt_type': 'agent_recipe',
        'agent_pattern': 'react',
        'content_override': 'B2B SaaS 브랜드 기준 인스타 3편·링크드인 2편 주간 캘린더. 최근 성과 좋은 포스트 톤을 참고.',
        'workflow_steps': [
            {
                'step': 1, 'name': '성과 참고',
                'system_message': '지난 4주 게시물 중 engagement 상위 3개의 주제·톤·포맷 패턴 요약',
                'tool': 'analytics_api',
            },
            {
                'step': 2, 'name': '주제 선정',
                'system_message': '이번 주 프로모션·블로그 신규 글·업계 이슈 중 5개 훅 후보 생성',
                'tool': 'ideation',
            },
            {
                'step': 3, 'name': '캘린더 작성',
                'system_message': '요일·플랫폼·캡션 초안(인스타 100자, 링크드인 200자)·해시태그 5개를 표로',
                'tool': 'calendar_builder',
            },
        ],
    },
]

PROMPTS.extend(EXTRA_PROMPTS)
PROMPTS.extend(AGENT_RECIPE_PROMPTS)
PROMPTS.extend(AGENT_RECIPE_EXTRA)

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
