"""ALLOWED_HOSTS 구성 — Vercel 배포 도메인 자동 반영."""
import os


def _normalize_host(value: str) -> str:
    host = value.strip().removeprefix('https://').removeprefix('http://')
    return host.split('/')[0].split(':')[0]


def vercel_hosts() -> list[str]:
    """Vercel 런타임 환경 변수에서 허용 호스트를 수집한다."""
    if not os.environ.get('VERCEL'):
        return []

    hosts: list[str] = ['.vercel.app']
    for key in ('VERCEL_URL', 'VERCEL_PROJECT_PRODUCTION_URL', 'VERCEL_BRANCH_URL'):
        raw = os.environ.get(key, '')
        if not raw:
            continue
        host = _normalize_host(raw)
        if host and host not in hosts:
            hosts.append(host)
    return hosts


def build_allowed_hosts(raw: str) -> list[str]:
    hosts = [_normalize_host(h) for h in raw.split(',') if h.strip()]
    for host in vercel_hosts():
        if host not in hosts:
            hosts.append(host)
    return hosts
