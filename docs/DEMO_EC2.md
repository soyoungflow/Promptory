# Phase 4 EC2 시연 (Docker Compose + nginx)

[DECISIONS.md](./phases/DECISIONS.md), [WBS_SCHEDULE_0602_0608.md](./phases/WBS_SCHEDULE_0602_0608.md), 4차 평가 자가정검 체크리스트와 정렬되어 있습니다.

**프록시 상세:** 경로 매핑, 설정 파일, 트러블슈팅 → [NGINX_REVERSE_PROXY.md](./NGINX_REVERSE_PROXY.md)

## 스택 (8개 서비스, 외부 포트 1개)

| 경로 | 용도 |
|------|------|
| `http://<EC2_HOST>/` | Django 메인 UI |
| `http://<EC2_HOST>/blueprints/new/` | **설계서 만들기** (4차 핵심 시연) |
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
docker compose exec web python manage.py collectstatic --noinput
```

**EC2 `.env` 예시:**

```bash
ALLOWED_HOSTS=localhost,127.0.0.1,web,13.211.8.186
PUBLIC_BASE_URL=http://13.211.8.186
LLM_PROVIDER=mock
```

## HF 시연 (평가용만)

HF 시연: **[HF_EC2_SETUP.md](./HF_EC2_SETUP.md)** (2GB EC2는 mock; HF는 **t3.medium 4GB+** 권장)

```bash
# EC2 .env
LLM_PROVIDER=huggingface
HF_MODEL_NAME=LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct
HF_EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
HF_TORCH_DTYPE=float16
docker compose build ai_server && docker compose up -d ai_server celery_worker
```

리허설·본 발표 흐름은 **mock** 유지 권장. HF는 짧은 시연 또는 `/ai/docs`용.

## 21단계 시연 스크립트 (요약)

1. 홈 → 프롬프트·레시피 탐색 (3차 유지)
2. 작성자 계정으로 로그인
3. 상단 **설계서 만들기** (`/blueprints/new/`) — 자동화 요청·추가 맥락 입력
4. **변환 시작** → `POST /api/prompts/{id}/transform/` → `task_id`·`status_url` 반환
5. DevTools: **`GET /api/tasks/{task_id}/status/`** 폴링 → PENDING → PROCESSING → SUCCESS
6. SUCCESS 후 **`GET /api/blueprints/design/{id}/`** 로 4단계 설계 결과 + confidence 표시
7. (선택) **레시피로 등록** — 마켓 초안 공개
8. 보관함 → **내 에이전트 설계서** 탭
9. (4~6과 동일) Network 탭에서 `transform` → `tasks/.../status/` → `blueprints/design/` 순서 확인
10. `http://<EC2_HOST>/ai/docs` → `/transform` mock 호출
11. `http://<EC2_HOST>/prometheus/` targets UP, Grafana 대시보드
12. Admin → Task / AgentTransformation / BlueprintDesign 행 확인

> **참고:** 레시피 상세 페이지의 인라인 「에이전트로 변환하기」는 제거됨 (DECISIONS Q15). 시연은 **설계서 만들기** 경로를 사용하세요.

## 디스크 (CD 실패 시)

EC2 기본 8GB EBS는 HF 이미지 재빌드 시 **디스크 부족**이 날 수 있습니다.

```bash
# SSH 접속 후
docker compose down
docker builder prune -af && docker system prune -af
df -h /
```

여유가 2GB 미만이면 EBS를 **20GB** 이상으로 확장하세요. 상세: [troubleshooting.md §9](./troubleshooting.md#9-cd-배포-실패--no-space-left-on-device)

## 보안 그룹

**인바운드 TCP 80** 만 열면 됩니다 (시연용 Source: `0.0.0.0/0` 또는 `내 IP/32`).

SSH(22)는 배포·관리용으로 별도 유지.

## EC2 기존 gunicorn + 호스트 nginx

80번 충돌 시 → [NGINX_REVERSE_PROXY.md §5](./NGINX_REVERSE_PROXY.md#5-배포-절차) 참고.

## 부하 테스트 (가산점)

```bash
k6 run -e BASE_URL=http://13.211.8.186 scripts/k6/smoke.js
```

→ [BONUS_POINTS_PLAN.md](./BONUS_POINTS_PLAN.md)
