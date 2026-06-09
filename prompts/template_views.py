"""
Template Views — 화면 렌더링 전용.
데이터 처리는 없음. DRF API(/api/...)가 담당.
JS가 API를 호출해 DOM을 채운다.
"""
from django.shortcuts import render


def home(request):
    """GET / — Promptory 홈 화면"""
    return render(request, 'prompts/home.html')


def prompt_list(request):
    """GET /prompts/ — 프롬프트 목록 페이지"""
    return render(request, 'prompts/list.html')


def library(request):
    """GET /library/ — 북마크 + 내가 등록한 프롬프트 (JWT 기준, 화면만)"""
    return render(request, 'prompts/library.html')


def prompt_detail(request, pk):
    """GET /prompts/<pk>/ — 프롬프트 상세 페이지"""
    return render(request, 'prompts/detail.html', {'prompt_id': pk})


def blueprint_design(request, pk=None):
    """GET /blueprints/new/ 또는 /blueprints/<pk>/ — 설계서 만들기 위저드."""
    return render(request, 'prompts/blueprint_design.html', {'design_id': pk or ''})


def prompt_create(request):
    """GET /prompts/new/ — 프롬프트 등록 페이지.

    JWT-only 인증이므로 접근 제어는 prompt-form.js가 토큰 기준으로 처리한다.
    """
    return render(request, 'prompts/form.html', {'is_edit': False, 'mode': 'create'})


def prompt_edit(request, pk):
    """GET /prompts/<pk>/edit/ — 프롬프트 수정 페이지.

    JWT-only 인증이므로 접근 제어는 API 권한과 프론트 토큰 검사에 맡긴다.
    """
    return render(request, 'prompts/form.html', {'prompt_id': pk, 'is_edit': True, 'mode': 'edit'})
