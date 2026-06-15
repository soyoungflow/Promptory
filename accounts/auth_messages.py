"""SimpleJWT / JWT 인증 오류를 사용자용 한국어로 통일."""

from __future__ import annotations

from typing import Any

# rest_framework_simplejwt locale/ko_KR/LC_MESSAGES/django.po 기준
_LIBRARY_KO_TO_FRIENDLY: dict[str, str] = {
    '인증 헤더에는 공백으로 구분 된 두 개의 값이 포함되어야 합니다': (
        '인증 정보 형식이 올바르지 않습니다.'
    ),
    '이 토큰은 모든 타입의 토큰에 대해 유효하지 않습니다': (
        '로그인 정보가 올바르지 않습니다. 다시 로그인해 주세요.'
    ),
    '토큰에 사용자 식별자가 포함되어 있지 않습니다': (
        '로그인 정보를 확인할 수 없습니다. 다시 로그인해 주세요.'
    ),
    '찾을 수 없는 사용자입니다': '계정을 찾을 수 없습니다.',
    '비활성화된 사용자입니다': '비활성화된 계정입니다.',
    "사용자의 비밀번호가 바뀌었습니다.": '비밀번호가 변경되어 다시 로그인해야 합니다.',
    '유효하지 않거나 만료된 토큰입니다': '로그인이 만료되었습니다. 다시 로그인해 주세요.',
    '지정된 자격 증명에 해당하는 활성화된 사용자를 찾을 수 없습니다': (
        '이메일 또는 비밀번호가 올바르지 않습니다.'
    ),
    '잘못된 토큰 타입입니다': '로그인 정보가 올바르지 않습니다. 다시 로그인해 주세요.',
    '토큰 타입이 주어지지 않았습니다': '로그인 정보가 올바르지 않습니다. 다시 로그인해 주세요.',
    '토큰에 식별자가 주어지지 않았습니다': '로그인 정보가 올바르지 않습니다. 다시 로그인해 주세요.',
    '블랙리스트에 추가된 토큰입니다': '이미 로그아웃된 세션입니다. 다시 로그인해 주세요.',
}

# 영문 msgid — LANGUAGE_CODE 변경 시 대비
_MSGID_TO_FRIENDLY: dict[str, str] = {
    'Authorization header must contain two space-delimited values': (
        '인증 정보 형식이 올바르지 않습니다.'
    ),
    'Given token not valid for any token type': (
        '로그인 정보가 올바르지 않습니다. 다시 로그인해 주세요.'
    ),
    'Token contained no recognizable user identification': (
        '로그인 정보를 확인할 수 없습니다. 다시 로그인해 주세요.'
    ),
    'User not found': '계정을 찾을 수 없습니다.',
    'User is inactive': '비활성화된 계정입니다.',
    "The user's password has been changed.": '비밀번호가 변경되어 다시 로그인해야 합니다.',
    'Token is invalid or expired': '로그인이 만료되었습니다. 다시 로그인해 주세요.',
    'No active account found with the given credentials': (
        '이메일 또는 비밀번호가 올바르지 않습니다.'
    ),
    'Token has wrong type': '로그인 정보가 올바르지 않습니다. 다시 로그인해 주세요.',
    'Token has no type': '로그인 정보가 올바르지 않습니다. 다시 로그인해 주세요.',
    'Token has no id': '로그인 정보가 올바르지 않습니다. 다시 로그인해 주세요.',
    'Token is blacklisted': '이미 로그아웃된 세션입니다. 다시 로그인해 주세요.',
}

_CODE_TO_FRIENDLY: dict[str, str] = {
    'no_active_account': '이메일 또는 비밀번호가 올바르지 않습니다.',
    'token_not_valid': '로그인이 만료되었습니다. 다시 로그인해 주세요.',
}

_DEFAULT_FRIENDLY = '로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.'


def _extract_text(raw: Any) -> str:
    if raw is None:
        return ''
    if isinstance(raw, dict):
        return _extract_text(raw.get('detail') or raw.get('message') or '')
    if isinstance(raw, (list, tuple)):
        return _extract_text(raw[0]) if raw else ''
    return str(raw).strip()


def friendly_auth_detail(raw: Any, *, code: str | None = None) -> str:
    """SimpleJWT/DRF 인증 오류를 화면용 한국어로 변환."""
    if code and code in _CODE_TO_FRIENDLY:
        return _CODE_TO_FRIENDLY[code]

    text = _extract_text(raw)
    if not text:
        return _DEFAULT_FRIENDLY

    return (
        _LIBRARY_KO_TO_FRIENDLY.get(text)
        or _MSGID_TO_FRIENDLY.get(text)
        or _CODE_TO_FRIENDLY.get(text)
        or text
    )
