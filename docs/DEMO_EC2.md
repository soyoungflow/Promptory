# Phase 4 EC2 시연 (Docker Compose + nginx)

[DECISIONS.md](./phases/DECISIONS.md), [WBS_SCHEDULE_0602_0608.md](./phases/WBS_SCHEDULE_0602_0608.md), 4차 평가 자가정검 체크리스트와 정렬되어 있습니다.

**프록시 상세:** 경로 매핑, 설정 파일, 트러블슈팅 → [NGINX_REVERSE_PROXY.md](./NGINX_REVERSE_PROXY.md)

## 스택 (8개 서비스, 외부 포트 1개)

| 경로 | 용도 |
|------|------|
| `http://<EC2_HOST>/` | Django 메인 UI |
| `http://<EC2_HOST>/ai/docs` | FastAPI Swagger |
| `http://<EC2_HOST>/ai/health` | AI 서버 헬스 |
| `http://<EC2_HOST>/grafana/` | Grafana (admin / admin) |
| `http://<EC2_HOST>/prometheus/` | Prometheus |

`nginx`가 **80번**만 받아 내부 서비스로 분기합니다. Celery·Redis·Postgres는 외부 포트 없음.

## 배포 (기존 CD 또는 수동)

```bash
cd /path/to/Promptory
git pull origin main
cp .env.example .env   # 최초 1회 — SECRET_KEY, ALLOWED_HOSTS, PUBLIC_BASE_URL 설정
docker compose up -d --build
docker compose exec web python manage.py migrate --noinput
```

**EC2 `.env` 예시:**

```bash
ALLOWED_HOSTS=localhost,127.0.0.1,web,13.211.8.186
PUBLIC_BASE_URL=http://13.211.8.186
LLM_PROVIDER=mock
```

## HF 시연 (평가용만)

```bash
# EC2 .env
LLM_PROVIDER=huggingface
```

HF 의존성이 포함된 `ai_server` 이미지로 재빌드 후, 첫 모델 다운로드에 10~15분 소요될 수 있습니다. 리허설은 **mock**(기본값) 사용을 권장합니다.

## 21단계 시연 스크립트 (요약)

1. 홈 → 프롬프트 탐색 (3차 유지)
2. 작성자 계정으로 로그인
3. 본인 프롬프트 상세 → **에이전트로 변환하기**
4. PENDING → SUCCESS 표시 (폴링 또는 WebSocket)
5. 인라인 4단계 에이전트 결과 + confidence
6. 보관함 → **내 변환** 탭 (프롬프트당 최신 1건)
7. DevTools: `GET /api/tasks/{id}/status/`
8. `http://<EC2_HOST>/ai/docs` → `/transform` mock 호출
9. `http://<EC2_HOST>/prometheus/` targets UP, Grafana 대시보드
10. Admin → Task / AgentTransformation 행 확인

## 보안 그룹

**인바운드 TCP 80** 만 열면 됩니다 (시연용 Source: `0.0.0.0/0` 또는 `내 IP/32`).

SSH(22)는 배포·관리용으로 별도 유지.

## EC2 기존 gunicorn + 호스트 nginx

80번 충돌 시 → [NGINX_REVERSE_PROXY.md §5](./NGINX_REVERSE_PROXY.md#5-배포-절차) 참고.
