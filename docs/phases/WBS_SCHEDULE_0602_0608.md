# WBS 일정 — 2026년 6월 2일~8일 (Phase 4)

부트캠프 **4차** 납품을 위한 **EC2 + Docker Compose** 일별 작업 계획입니다.

**관련 문서**

- [DECISIONS.md](./DECISIONS.md) — 확정 Q1~Q12
- [PHASE_4_PLANNED.md](./PHASE_4_PLANNED.md) — 기능·아키텍처 맵
- [DEMO_EC2.md](../DEMO_EC2.md) — 배포 URL 및 짧은 시연 스크립트
- [NGINX_REVERSE_PROXY.md](../NGINX_REVERSE_PROXY.md) — 단일 포트 80 프록시
- [4차 발표가이드 및 평가기준.md](../4차 발표가이드 및 평가기준.md)
- [자가정검 체크리스트(개인프로젝트).md](../자가정검 체크리스트(개인프로젝트).md)

---

## 현재 진행 스냅샷 (2026-06-05 갱신)

| 구분 | 상태 | 비고 |
|------|------|------|
| **저장소 코드 (Phase 3)** | ✅ 완료 | JWT, CRUD, interaction, 보관함, CI 테스트 |
| **저장소 코드 (Phase 4)** | ✅ 구현됨 | 모델·API·Celery·FastAPI·WS·UI·모니터링 설정 파일 존재 |
| **GitHub CI** | ✅ 동작 | Postgres + `manage.py test` + compose-smoke (healthy 대기) |
| **GitHub CD** | ✅ SSH 연결 + 자동 배포 | `main` push 시 EC2 `git sync` → `compose up` → healthy 대기 → smoke |
| **EC2 Compose 7서비스** | 🟡 부분 검증 | CD 로그: migrate OK, `ai_server` health OK, `web`은 기동 후 daphne 200 |
| **EC2 외부 시연 URL** | 🟡 부분 | Docker nginx `:80` — `http://<EC2>/`, `/ai/docs` 등 ([프록시 문서](../NGINX_REVERSE_PROXY.md)) |
| **증빙·리허설** | 🔴 미완 | 스크린샷, ERD PNG, 발표 리허설, k6 결과 캡처 |
| **자동 테스트** | ✅ | 39 tests (accounts, prompts, interaction, ai_gateway, tasks) |
| **문서** | ✅ | `troubleshooting.md`, `API_PHASE4.md`, `BONUS_POINTS_PLAN.md` |

**핵심 메시지:** 남은 일은 **새 기능 코딩**보다 **EC2에서 E2E 검증 + 보안 그룹 + 증빙 캡처 + 발표 리허설**이다.

### CD 배포 메모 (2026-06-01 이슈 해결)

`docker compose up` 직후 `web`은 `migrate → daphne` 순으로 기동하므로 `(health: starting)` 상태에서 curl 시 `Empty reply`가 날 수 있다.

`.github/workflows/cd.yml`에 아래가 반영됨:

1. `wait_for_healthy ai_server` / `wait_for_healthy web` (최대 180초)
2. 그 후 `migrate` + `curl --retry-all-errors`

---

## 개요

| 항목 | 내용 |
|------|------|
| **기간** | 2026-06-02 (화) ~ 2026-06-08 (월) |
| **WBS 매핑** | Day 2 ~ Day 8 (Day 1 = 6/01 인프라) |
| **배포 대상** | EC2 + `docker compose` (7서비스) — 4차 시연 주 호스트는 Vercel 아님 |
| **코드 기준선** | Phase 4 구현은 저장소에 반영됨; 이번 주는 **검증, seed, 증빙, 리허설** 중심 |

### 저장소에 이미 있는 것 (코드 ✅)

- `docker-compose.yml` — db, redis, web, ai_server, celery_worker, prometheus, grafana, **nginx** (외부 `:80`만)
- Models: `Prompt` 확장, `AgentTransformation`, `PromptEmbedding`, `Task`
- FastAPI `ai_server/` — mock + 선택 HF 로더 (`/health`, `/transform`, `/embed`)
- Celery: `tasks/celery_tasks.py` — `transform_prompt`, `embed_prompt`
- APIs: transform, task status, agent JSON, similar, `me/transformations/`
- UI: **설계서 만들기** (`/blueprints/new/`, `blueprint-design.js`), 보관함 「내 변환」 (`library.js`), 폼 `prompt_type`
- WebSocket: `ws/tasks/?token=` + 폴링 fallback
- 모니터링: `prometheus/prometheus.yml`, `grafana/provisioning/`, `monitoring/metrics.py`
- CD: `.github/workflows/cd.yml` — SSH 배포 + healthy 대기 + smoke check

### 아직 저장소/EC2에 없는 것 (남은 작업 🔴)

- ERD PNG export (mermaid → 이미지) — [DATA_MODEL_BY_PHASE.md](./DATA_MODEL_BY_PHASE.md)
- EC2 브라우저 E2E (설계서 만들기 경로)
- k6 실행 결과 캡처 (`scripts/k6/smoke.js`)
- 발표 증빙 패키지 (스크린샷·리허설 영상 등)

### 이번 주에 증명해야 할 것

자가정검 체크리스트 E2E 흐름:

> 사용자 입력 → Django → DB → AI 요청 → **비동기 (Celery)** → 결과 DB 저장 → **설계서 UI** (`/blueprints/new/`) → **모니터링**

---

## 일별 완료 기준 (한눈에)

| 날짜 | WBS day | 한 줄 「완료」 | 진행 |
|------|---------|----------------|------|
| **06-01** | Day 1 | SSH/CD 연결, Secrets 설정 | ✅ |
| **06-02** | Day 2 | migrate 적용; Admin 4차 모델; Phase 3 정상 | 🟡 |
| **06-03** | Day 3 | `/ai/health` OK; `/ai/docs` transform (mock) OK | 🟡 |
| **06-04** | Day 4 | `celery_worker` ready; Task PENDING → SUCCESS | 🔴 |
| **06-05** | Day 5 | 설계서 만들기 → 4단계 결과 + 보관함 「내 변환」 | 🔴 |
| **06-06** | Day 6 | Prometheus targets UP; Grafana 스크린샷 | 🔴 |
| **06-07** | Day 7 | WebSocket + 폴링 fallback; 콜드 스타트 리허설 | 🔴 |
| **06-08** | Day 8 | 라이브 발표 + 증빙 패키지 제출 | 🔴 |

범례: ✅ 완료 · 🟡 부분 완료 · 🔴 미완

---

## 공통 명령 (EC2)

EC2 프로젝트 루트 (`$EC2_APP_DIR`)에서:

```bash
# 스택 기동 / 재빌드 (CD가 push마다 자동 실행)
docker compose up -d --build

# web·ai_server healthy 대기 (CD 스크립트와 동일 패턴)
for i in $(seq 1 60); do
  WEB=$(docker inspect --format='{{.State.Health.Status}}' "$(docker compose ps -q web)" 2>/dev/null)
  AI=$(docker inspect --format='{{.State.Health.Status}}' "$(docker compose ps -q ai_server)" 2>/dev/null)
  echo "web=$WEB ai_server=$AI"
  [ "$WEB" = "healthy" ] && [ "$AI" = "healthy" ] && break
  sleep 3
done

# 마이그레이션 (스키마 변경 후)
docker compose exec -T web python manage.py migrate --noinput

# 샘플 데이터 (최초 1회 또는 리셋 후)
docker compose exec -T web python manage.py seed_mockup

# 상태 및 로그
docker compose ps
docker compose logs celery_worker --tail 50
docker compose logs ai_server --tail 50
docker compose logs web --tail 50

# 헬스 체크 (EC2 내부 — nginx 경유)
curl -fsS http://127.0.0.1/
curl -s http://127.0.0.1/ai/health
```

**환경 (리허설 권장):**

```bash
# EC2 .env
LLM_PROVIDER=mock
FASTAPI_URL=http://ai_server:8000
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

**보안 그룹 (시연 필수):** **TCP 80** 개방 (+ SSH 22). 상세 → [NGINX_REVERSE_PROXY.md](../NGINX_REVERSE_PROXY.md).

> 참고: 현재 `:80` Nginx(구 배포)만 외부 접근 가능. Phase 4 시연은 **Compose 포트(8000 등)** 기준이므로 SG 개방 또는 Nginx 리버스 프록시 전환 필요.

---

## 6월 1일 (일) — Day 1 · 인프라 / CD

**WBS 목표:** EC2 접속, GitHub Secrets, CD 파이프라인.

### 진행 체크리스트

- [x] GitHub Secrets: `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `EC2_PORT`, `EC2_APP_DIR`
- [x] CD SSH 연결 성공 (`appleboy/ssh-action`)
- [x] CD 자동 배포 스크립트 (`git sync` → `compose up` → healthy 대기 → smoke)
- [x] CD health check 타이밍 이슈 해결 (`wait_for_healthy` 추가)
- [ ] EC2 `.env` Phase 4 변수 최종 확인 (`LLM_PROVIDER=mock` 등)
- [ ] EC2 보안 그룹 Phase 4 포트 개방

---

## 6월 2일 (화) — Day 2 · 데이터 모델

**WBS 목표:** 도메인 스키마 확장, AI 결과 테이블, Task 모델, Admin, migrations, seed.

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | EC2에 최신 `main` 배포 | CD 자동 또는 `git pull` → `docker compose up -d --build` |
| 2 | 마이그레이션 실행 | CD 로그: `No migrations to apply` 확인됨 |
| 3 | Admin 테이블 확인 | `AgentTransformation`, `PromptEmbedding`, `Task`; Prompt 확장 필드 |
| 4 | Seed | `seed_mockup` — **3× `agent_recipe`** 예시 |
| 5 | ERD 증빙 | [DATA_MODEL_BY_PHASE.md](./DATA_MODEL_BY_PHASE.md) → mermaid.live → PNG |
| 6 | Phase 3 회귀 | 가입/로그인, CRUD, 댓글, 좋아요, 북마크, 검색, 페이지네이션 |

### 진행 체크리스트

- [x] EC2 CD 배포 파이프라인 (`main` push → SSH deploy)
- [x] EC2 migrate (CD 6단계 — 적용할 migration 없음 확인)
- [x] 스키마/코드 준비:
  - `Prompt`: `prompt_type`, `workflow_steps`, `agent_pattern`
  - `ai_gateway`: `AgentTransformation`, `PromptEmbedding`
  - `tasks`: `Task` (UUID + status)
- [x] Seed 코드 **3× `agent_recipe`** (`seed_mockup.py`)
- [ ] EC2에서 `seed_mockup` 실행 및 Admin 데이터 확인
- [ ] ERD 이미지 export (mermaid.live → PNG)
- [x] Phase 3 회귀 테스트 (로컬/sqlite_legacy — 19 passed)
- [ ] Phase 3 회귀 **EC2 브라우저** 스모크 (`http://<EC2>/`)

### 종료 기준

- 핵심 모델과 **AI 결과가 별도 테이블**임을 설명 가능 (`Prompt.content` 덮어쓰지 않음).
- 자가정검 §2 (3차 유지), §3 (데이터 구조) 일부 충족.

### 캡처할 증빙

- [ ] Admin 스크린샷: Task + AgentTransformation 목록
- [ ] 발표용 ERD 이미지

---

## 6월 3일 (수) — Day 3 · FastAPI + AI server

**WBS 목표:** 독립 AI 서버, mock/HF, `/health`, `/transform`, `/embed`.

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | 컨테이너 health | `docker compose ps` — `ai_server` healthy |
| 2 | Health | EC2 내부 `curl http://127.0.0.1/ai/health` → `ok`, `provider: mock` |
| 3 | FastAPI docs | `http://<EC2>/ai/docs` |
| 4 | 수동 transform | POST `/transform` 샘플 → 4단계 JSON |
| 5 | 리허설 mock 고정 | EC2 `.env`에 `LLM_PROVIDER=mock` |
| 6 | HF 준비 (선택) | 첫 실행 10~15분 — 리허설 필수 아님 |

### 진행 체크리스트

- [x] `ai_server` 코드·Dockerfile·healthcheck (`docker-compose.yml`)
- [x] EC2 **내부** health: `{"status":"ok","provider":"mock"}` (CD 로그 확인)
- [ ] EC2 **외부** `http://<EC2>/ai/docs` 접근
- [ ] POST `/transform` 수동 호출 증빙

### 종료 기준

- **Django가 모델을 돌리지 않고 FastAPI가 돈다**는 설명 가능.
- 자가정검 §4-2, §4-3 (FastAPI 분리, 엔드포인트).

### 캡처할 증빙

- [ ] `/docs` 스크린샷
- [ ] `/transform` 샘플 응답 (JSON 또는 Swagger UI)

---

## 6월 4일 (목) — Day 4 · Celery + Redis

**WBS 목표:** 비동기 Worker, Task 상태 머신, Django → FastAPI httpx.

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | Redis | `docker compose exec redis redis-cli ping` → `PONG` |
| 2 | Celery worker | `docker compose logs celery_worker` — `ready` |
| 3 | Task 생명주기 | 변환 트리거; Admin에서 PENDING → PROCESSING → SUCCESS |
| 4 | 실패 경로 | 선택: `ai_server` 중지 → Task FAIL + `error_message` |
| 5 | 생성 시 embed | 새 프롬프트 → `task_type=embed` (`prompts/signals.py`) |

### 진행 체크리스트

- [x] Redis·Celery·`tasks/celery_tasks.py` 코드 존재
- [ ] EC2 `celery_worker` 로그 `ready` 확인
- [ ] 변환 1회 → Admin Task SUCCESS + `result_id`
- [ ] (선택) FAIL 경로 1회 재현

### 종료 기준

- 즉시 **202 + task_id**; 긴 작업은 HTTP 스레드 밖.
- 자가정검 §5-1 ~ §5-3 (Celery + Redis, Task 생성, 4단계 상태).

### 캡처할 증빙

- [ ] Celery 로그: `transform_success` 등
- [ ] Admin: SUCCESS Task + `result_id`

---

## 6월 5일 (금) — Day 5 · API + UI (핵심 시연 경로) ⭐

**WBS 목표:** Transform API, 상태 폴링, 상세 **인라인** 에이전트 UI, 보관함 탭.

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | **작성자**로 로그인 | 비작성자는 변환 버튼 없음 (Q7) |
| 2 | 상세 페이지 | 본인 프롬프트 → **에이전트로 변환하기** |
| 3 | UX | 「변환 중…」 → mock ~2~3s → **4단계 + confidence** 인라인 |
| 4 | Network | `POST .../transform/` → `GET .../tasks/{id}/status/` → `GET .../agent/` |
| 5 | 보관함 | 탭 **내 변환** — 소유 프롬프트당 최신 1건 (Q3) |
| 6 | 유사 프롬프트 | 2건 이상 embed SUCCESS 후 상세 유사 목록 |
| 7 | 전체 스크립트 1회 | 홈 → 탐색 → 로그인 → 변환 → 보관함 |

### 진행 체크리스트

- [x] API·UI 코드: `ai_gateway/views.py`, `prompt-detail.js`, `library.js`
- [ ] EC2 `http://<EC2>/` 에서 **브라우저 E2E 1회** 통과
- [ ] DevTools Network 탭 증빙 캡처

### 종료 기준

- 발표 (2) AI 연결 + (3) 비동기 사용자 스토리 완결.
- 자가정검 §4-4, §5-4, §5-5.

### 캡처할 증빙

- [ ] 인라인 4단계 상세 화면
- [ ] 보관함 「내 변환」 탭
- [ ] DevTools: task status JSON

---

## 6월 6일 (토) — Day 6 · 모니터링 + 유사도

**WBS 목표:** Prometheus, Grafana, `/metrics`, 임베딩 유사도.

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | Prometheus | `http://<EC2>/prometheus/targets` — `django`, `fastapi` **UP** |
| 2 | Django metrics | `http://<EC2>/metrics` (또는 내부 `web:8000/metrics`) |
| 3 | Grafana | `http://<EC2>/grafana/` (admin/admin) |
| 4 | 대시보드 | 변환 2~3회로 그래프 채우기 |
| 5 | 유사도 | `GET /api/prompts/{id}/similar/` |
| 6 | 자가정검 §7~10 | 라이브 시연 가능한 항목만 `[x]` |

### 진행 체크리스트

- [x] `prometheus/prometheus.yml`, `grafana/provisioning/` 코드 존재
- [ ] EC2 Prometheus targets **UP** 확인
- [ ] Grafana 대시보드 스크린샷
- [ ] 유사 프롬프트 API 1회 이상 동작 확인

### 종료 기준

- 발표 (5) 모니터링 + 배포 구조.
- 가산: Prometheus + Grafana + 커스텀 메트릭.

### 캡처할 증빙

- [ ] Prometheus targets UP
- [ ] Grafana 대시보드 스크린샷

---

## 6월 7일 (일) — Day 7 · WebSocket + 안정화

**WBS 목표:** WS 태스크 알림, 폴링 fallback, troubleshooting, 전체 재기동 리허설.

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | WebSocket | DevTools → `ws/tasks/?token=...` |
| 2 | Fallback | WS 차단 시 폴링으로 SUCCESS (Q11) |
| 3 | Troubleshooting | `docs/troubleshooting.md` — 3시나리오 |
| 4 | 콜드 스타트 | `docker compose down` → `up -d --build` → 시연 1회 |
| 5 | 슬라이드 초안 | 발표 가이드 15분 개요 |
| 6 | 포트 / SG | EC2 보안 그룹 최종 |

### 진행 체크리스트

- [x] WebSocket 코드: `config/asgi.py`, `tasks/consumers.py`, `prompt-detail.js`
- [ ] EC2에서 WS 연결 DevTools 캡처
- [ ] 폴링 fallback 1회 확인
- [x] `docs/troubleshooting.md` 작성
- [ ] 콜드 스타트 리허설 1회

### 종료 기준

- 시연 중 장애 시 복구 스토리 준비.
- 자가정검 §5-5 (WS 또는 폴링), §7 (예외/로그).

### 캡처할 증빙

- [ ] DevTools WS 연결
- [ ] (선택) FAIL Task + `error_message`

---

## 6월 8일 (월) — Day 8 · 시연 + 발표

**WBS 목표:** 라이브 21단계, 리허설 3회, 제출 패키지.

### 권장 라이브 흐름 (10~15분)

| Step | 내용 | ~분 |
|------|------|-----|
| 1 | 문제, 사용자, 3차→4차 진화 | 1.5 |
| 2 | 아키텍처 (7 컨테이너) | 1.5 |
| 3 | Phase 3: 탐색, 로그인 | 1 |
| 4 | **설계서 만들기** → Task → 4단계 결과 | 3 |
| 5 | 보관함 「내 변환」 | 1 |
| 6 | FastAPI `/docs` + `/transform` 1회 | 1 |
| 7 | Prometheus + Grafana | 2 |
| 8 | Admin: Task / AgentTransformation | 0.5 |
| 9 | 한계 (mock 기본, 결제·analyze MVP 없음) + 로드맵 | 1 |

### 증빙 제출 체크리스트

- [ ] 메인 UI / 변환 결과
- [ ] `docker compose ps` (7서비스)
- [ ] FastAPI `/docs`
- [ ] Celery 로그 또는 Admin Task SUCCESS
- [ ] Prometheus targets UP
- [ ] Grafana 대시보드
- [ ] (선택) FAIL + `error_message`
- [ ] 표지 슬라이드 GitHub / 배포 URL

### 종료 기준

- 자가정검에서 `[x]` 한 항목은 즉흥 없이 시연 가능.
- 평가: 「AI + 운영 백엔드」 스토리 완결.

---

## 평가 루브릭 매핑

| 루브릭 영역 | 주요 날짜 | 코드 | EC2 검증 |
|-------------|-----------|------|----------|
| 3차 서비스 유지 | 06-02, 06-05 | ✅ | 🔴 |
| AI + 서버 분리 | 06-03, 06-05 | ✅ | 🟡 |
| AI 결과 DB + API/UI | 06-02, 06-05 | ✅ | 🔴 |
| 비동기 (Celery + Redis) | 06-04, 06-05 | ✅ | 🔴 |
| Task 상태 4단계 | 06-04, 06-05, 06-07 | ✅ | 🔴 |
| Docker Compose | 06-02 ~ 06-07 | ✅ | 🟡 |
| 모니터링 | 06-06 | ✅ | 🔴 |
| 배포 / 재현성 | 06-01, 06-07, 06-08 | ✅ | 🟡 |

---

## 이번 주 범위 밖 (DECISIONS)

| 항목 | 사유 |
|------|------|
| `AnalysisResult` / analyze task | Q4 — MVP 제외 |
| 유료 프롬프트 결제 | 비즈니스 phase 3 |
| 레시피 상세 인라인 변환 | Q15 — 설계서 만들기로 대체 |
| Vercel을 4차 주 호스트 | Q1 — EC2 Compose |
| `mcp_package` UI | Q8 — DB choice만, UI 비활성 |

---

## 시간이 부족할 때 우선순위 (갱신)

1. **지금 즉시:** EC2 SG **80** 개방 + `seed_mockup` + 브라우저 E2E (`/blueprints/new/` 경로)
2. **06-04:** Celery Task PENDING → SUCCESS Admin 증빙
3. **06-06:** Prometheus + Grafana 스크린샷
4. **06-07:** 콜드 스타트 리허설 1회
5. **06-08:** 리허설 ×3 + 증빙 패키지

코드 추가 개발보다 **EC2에서 보여줄 수 있게 만드는 것**이 우선이다.

---

## 문서 이력

| Date | Note |
|------|------|
| 2026-05-27 | WBS v2 + DECISIONS Q1~Q12 + 저장소 구현 상태로 초안 작성 |
| 2026-06-04 | 영어 문서 한글 번역 |
| 2026-06-05 | 코드·CD·EC2 점검 반영: Day 1 완료, Day 2~3 부분, Day 4~8 EC2 검증·증빙 미완 명시; CD `wait_for_healthy` 메모 추가 |
| 2026-06-08 | 설계서 만들기 시연 경로 반영, 39 tests·API_PHASE4·k6·자가정검 갱신 |
