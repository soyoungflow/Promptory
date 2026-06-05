# WBS 일정 — 2026년 6월 2일~8일 (Phase 4)

부트캠프 **4차** 납품을 위한 **EC2 + Docker Compose** 일별 작업 계획입니다.

**관련 문서**

- [DECISIONS.md](./DECISIONS.md) — 확정 Q1~Q12
- [PHASE_4_PLANNED.md](./PHASE_4_PLANNED.md) — 기능·아키텍처 맵
- [DEMO_EC2.md](../DEMO_EC2.md) — 배포 URL 및 짧은 시연 스크립트
- [4차 발표가이드 및 평가기준.md](../4차 발표가이드 및 평가기준.md)
- [자가정검 체크리스트(개인프로젝트).md](../자가정검 체크리스트(개인프로젝트).md)

---

## 개요

| 항목 | 내용 |
|------|------|
| **기간** | 2026-06-02 (화) ~ 2026-06-08 (월) |
| **WBS 매핑** | Day 2 ~ Day 8 (Day 1 = 6/01 인프라) |
| **배포 대상** | EC2 + `docker compose` (7서비스) — 4차 시연 주 호스트는 Vercel 아님 |
| **코드 기준선** | Phase 4 구현은 저장소에 반영됨; 이번 주는 **검증, seed, 증빙, 리허설** 중심 |

### 저장소에 이미 있는 것

- `docker-compose.yml` — db, redis, web (daphne), ai_server, celery_worker, prometheus, grafana
- Models: `Prompt` 확장, `AgentTransformation`, `PromptEmbedding`, `Task`
- FastAPI `ai_server/` — mock + 선택 HF 로더
- Celery tasks: `transform_prompt`, `embed_prompt`
- APIs: transform, task status, agent JSON, similar, `me/transformations/`
- UI: 상세 인라인 변환, 보관함 탭 「내 변환」, 폼 `prompt_type`
- WebSocket `ws/tasks/?token=` + 폴링 fallback

### 이번 주에 증명해야 할 것

자가정검 체크리스트 E2E 흐름:

> 사용자 입력 → Django → DB → AI 요청 → **비동기 (Celery)** → 결과 DB 저장 → **인라인 UI** → **모니터링**

---

## 일별 완료 기준 (한눈에)

| 날짜 | WBS day | 한 줄 「완료」 |
|------|---------|----------------|
| **06-02** | Day 2 | migrate 적용; Admin에 4차 모델 표시; Phase 3 기능 정상 |
| **06-03** | Day 3 | `:8001/health` OK; FastAPI `/docs` transform (mock) OK |
| **06-04** | Day 4 | `celery_worker` healthy; Task PENDING → SUCCESS (또는 FAIL + message) |
| **06-05** | Day 5 | 작성자 변환 → 인라인 4단계 + 보관함 「내 변환」 탭 |
| **06-06** | Day 6 | Prometheus targets UP; Grafana 스크린샷 |
| **06-07** | Day 7 | WebSocket + 폴링 fallback; 전체 스택 재기동 시연 통과 |
| **06-08** | Day 8 | 라이브 발표 + 증빙 패키지 제출 |

---

## 공통 명령 (EC2)

EC2 프로젝트 루트에서 `git pull` 후:

```bash
# 스택 기동 / 재빌드
docker compose up -d --build

# 마이그레이션 (스키마 변경 후)
docker compose exec web python manage.py migrate --noinput

# 샘플 데이터 (선택)
docker compose exec web python manage.py seed_mockup

# 상태 및 로그
docker compose ps
docker compose logs celery_worker --tail 50
docker compose logs ai_server --tail 50

# 헬스 체크
curl -s http://127.0.0.1:8001/health
curl -fsS http://127.0.0.1:8000/
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

**보안 그룹:** **8000**, **8001**, **9090**, **3000** 개방 (또는 시연 시 SSH 터널).

---

## 6월 2일 (화) — Day 2 · 데이터 모델

**WBS 목표:** 도메인 스키마 확장, AI 결과 테이블, Task 모델, Admin, migrations, seed.

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | EC2에 최신 `main` 배포 | `git pull` → `docker compose up -d --build` |
| 2 | 마이그레이션 실행 | `docker compose exec web python manage.py migrate --noinput` |
| 3 | Admin 테이블 확인 | `AgentTransformation`, `PromptEmbedding`, `Task`; Prompt에 `prompt_type`, `workflow_steps`, `agent_pattern` |
| 4 | Seed | `seed_mockup` — **3× `agent_recipe`** 예시 |
| 5 | ERD 증빙 | [DATA_MODEL_BY_PHASE.md](./DATA_MODEL_BY_PHASE.md)에서 mermaid.live → PNG |
| 6 | Phase 3 회귀 | 가입/로그인, CRUD, 댓글, 좋아요, 북마크, 검색, 페이지네이션 |

### 진행 체크리스트 (갱신)

- [ ] EC2 최신 `main` 배포 (`git pull` + `docker compose up -d --build`)
- [ ] EC2 migrate (`docker compose exec web python manage.py migrate --noinput`)
- [x] 스키마/코드 준비 확인:
  - `Prompt`에 `prompt_type`, `workflow_steps`, `agent_pattern`
  - `ai_gateway`: `AgentTransformation`, `PromptEmbedding`
  - `tasks`: `Task` (UUID + status)
- [x] Seed 코드 **3× `agent_recipe`** 및 필드 매핑 반영
- [ ] ERD 이미지 export (mermaid.live → PNG)
- [x] Phase 3 회귀 테스트 (`DJANGO_SETTINGS_MODULE=config.settings.sqlite_legacy manage.py test accounts prompts interaction` — 19 passed)

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
| 2 | Health | `curl http://<EC2>:8001/health` → `ok`, `provider: mock` |
| 3 | FastAPI docs | `http://<EC2>:8001/docs` |
| 4 | 수동 transform | POST `/transform` 샘플 `prompt_text` → 4단계 JSON |
| 5 | 리허설 mock 고정 | EC2 `.env`에 `LLM_PROVIDER=mock` (DECISIONS Q10) |
| 6 | HF 준비 (선택) | torch/transformers 이미지; 첫 실행 10~15분 — 일일 리허설 필수 아님 |

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
| 4 | 실패 경로 | 선택: `ai_server` 잠시 중지 → Task FAIL + `error_message` |
| 5 | 생성 시 embed | 새 프롬프트 → `task_type=embed` (`manage.py test` 시 스킵) |

### 종료 기준

- 즉시 **202 + task_id**; 긴 작업은 HTTP 스레드 밖.
- 자가정검 §5-1 ~ §5-3 (Celery + Redis, Task 생성, 4단계 상태).

### 캡처할 증빙

- [ ] Celery 로그: `transform_success` 등
- [ ] Admin: SUCCESS Task + `result_id`

---

## 6월 5일 (금) — Day 5 · API + UI (핵심 시연 경로)

**WBS 목표:** Transform API, 상태 폴링, 상세 **인라인** 에이전트 UI, 보관함 탭.

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | **작성자**로 로그인 | 비작성자는 변환 버튼 없음 (Q7) |
| 2 | 상세 페이지 | 본인 프롬프트 → **에이전트로 변환하기** |
| 3 | UX | 「변환 중… N초」 → mock ~2~3s → **4단계 + confidence** 인라인 |
| 4 | Network | `POST .../transform/` → `GET .../tasks/{id}/status/` → `GET .../agent/` |
| 5 | 보관함 | 탭 **내 변환** — 소유 프롬프트당 최신 1건 (Q3) |
| 6 | 유사 프롬프트 | 2건 이상 embed SUCCESS 후 상세 유사 목록 |
| 7 | 전체 스크립트 1회 | 홈 → 탐색 → 로그인 → 변환 → 보관함 |

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
| 1 | Prometheus | `http://<EC2>:9090/targets` — `django`, `fastapi` **UP** |
| 2 | Django metrics | `http://<EC2>:8000/metrics` |
| 3 | Grafana | `http://<EC2>:3000` (admin/admin); Prometheus datasource |
| 4 | 대시보드 | 트래픽·지연·태스크 결과; 변환 2~3회로 그래프 채우기 |
| 5 | 유사도 | 임베딩 후 `GET /api/prompts/{id}/similar/` |
| 6 | 자가정검 §7~10 | 라이브 시연 가능한 항목만 `[x]` |

### 종료 기준

- 발표 (5) 모니터링 + 배포 구조.
- 가산: Prometheus + Grafana + 커스텀 메트릭.

### 캡처할 증빙

- [ ] Prometheus targets UP
- [ ] Grafana 대시보드 스크린샷
- [ ] (선택) `agent_transformation_total` 등

---

## 6월 7일 (일) — Day 7 · WebSocket + 안정화

**WBS 목표:** WS 태스크 알림, 폴링 fallback, troubleshooting, 전체 재기동 리허설.

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | WebSocket | 변환 시 DevTools → `ws/tasks/?token=...`; 「실시간 알림 연결됨」 |
| 2 | Fallback | WS 차단 시에도 폴링으로 SUCCESS (Q11) |
| 3 | Troubleshooting | `docs/troubleshooting.md` — 3시나리오 (ai_server 지연, Celery broker, Prometheus scrape) |
| 4 | 콜드 스타트 | `docker compose down` → `up -d --build` → migrate → 시연 1회 |
| 5 | 슬라이드 초안 | 발표 가이드 15분 개요 |
| 6 | 포트 / SG | EC2 보안 그룹 최종 |

### 종료 기준

- 시연 중 장애 시 복구 스토리 준비.
- 자가정검 §5-5 (WS 또는 폴링), §7 (예외/로그).

### 캡처할 증빙

- [ ] DevTools WS 연결
- [ ] (선택) FAIL Task + `error_message` (한계/대응 슬라이드)

---

## 6월 8일 (월) — Day 8 · 시연 + 발표

**WBS 목표:** 라이브 21단계, 리허설 3회, 제출 패키지.

### 권장 라이브 흐름 (10~15분)

| Step | 내용 | ~분 |
|------|------|-----|
| 1 | 문제, 사용자, 3차→4차 진화 | 1.5 |
| 2 | 아키텍처 (7 컨테이너) | 1.5 |
| 3 | Phase 3: 탐색, 로그인 | 1 |
| 4 | **변환 버튼** → Task → 인라인 4단계 | 3 |
| 5 | 보관함 「내 변환」 | 1 |
| 6 | FastAPI `/docs` + `/transform` 1회 | 1 |
| 7 | Prometheus + Grafana | 2 |
| 8 | Admin: Task / AgentTransformation | 0.5 |
| 9 | 한계 (mock 기본, 결제·analyze MVP 없음) + 로드맵 | 1 |

### 작업

| # | Task | 비고 |
|---|------|------|
| 1 | 오전 점검 | `LLM_PROVIDER=mock`, 컨테이너 healthy |
| 2 | 리허설 ×3 | 동일 스크립트; 보여준 것만 주장 |
| 3 | 증빙 패키지 | 아래 체크리스트 |
| 4 | HF (선택) | HF 이미지 준비 시 30초만; 본 시연은 mock |

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

| 루브릭 영역 | 주요 날짜 |
|-------------|-----------|
| 3차 서비스 유지 | 06-02, 06-05 |
| AI + 서버 분리 | 06-03, 06-05 |
| AI 결과 DB + API/UI | 06-02, 06-05 |
| 비동기 (Celery + Redis) | 06-04, 06-05 |
| Task 상태 4단계 | 06-04, 06-05, 06-07 |
| Docker Compose | 06-02 ~ 06-07 |
| 모니터링 | 06-06 |
| 배포 / 재현성 | 06-02, 06-07, 06-08 |

---

## 이번 주 범위 밖 (DECISIONS)

| 항목 | 사유 |
|------|------|
| `AnalysisResult` / analyze task | Q4 — MVP 제외 |
| 유료 프롬프트 결제 | 비즈니스 phase 3 |
| 전용 `/prompts/{id}/agent/` 페이지 | Q2 — 인라인만 |
| Vercel을 4차 주 호스트 | Q1 — EC2 Compose |
| `mcp_package` UI | Q8 — DB choice만, UI 비활성 |

---

## 시간이 부족할 때 우선순위

1. **06-02:** EC2 deploy + `migrate` + Phase 3 스모크  
2. **06-05:** 전체 변환 시연 경로 (필수)  
3. **06-06:** Prometheus + Grafana 스크린샷  
4. **06-08:** 리허설 + 증빙  

나머지는 (2)가 EC2에서 동작할 때 점수를 보강합니다.

---

## 문서 이력

| Date | Note |
|------|------|
| 2026-05-27 | WBS v2 + DECISIONS Q1~Q12 + 저장소 구현 상태로 초안 작성 |
| 2026-06-04 | 영어 문서 한글 번역 |
