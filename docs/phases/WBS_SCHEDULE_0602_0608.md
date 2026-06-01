# WBS Schedule — June 2–8, 2026 (Phase 4)

Daily work plan for bootcamp **4차** delivery on **EC2 + Docker Compose**.

**Related docs**

- [DECISIONS.md](./DECISIONS.md) — locked Q1–Q12
- [PHASE_4_PLANNED.md](./PHASE_4_PLANNED.md) — feature & architecture map
- [DEMO_EC2.md](../DEMO_EC2.md) — deploy URLs & short demo script
- [4차 발표가이드 및 평가기준.md](../4차 발표가이드 및 평가기준.md)
- [자가정검 체크리스트(개인프로젝트).md](../자가정검 체크리스트(개인프로젝트).md)

---

## Overview

| Item | Detail |
|------|--------|
| **Period** | 2026-06-02 (Tue) ~ 2026-06-08 (Mon) |
| **WBS mapping** | Day 2 ~ Day 8 (Day 1 = 6/01 infrastructure) |
| **Deploy target** | EC2 + `docker compose` (7 services) — not Vercel for 4th demo |
| **Code baseline** | Phase 4 implementation is already in the repository; this week focuses on **verify, seed, evidence, rehearsal** |

### What is already in the repo

- `docker-compose.yml` — db, redis, web (daphne), ai_server, celery_worker, prometheus, grafana
- Models: `Prompt` extensions, `AgentTransformation`, `PromptEmbedding`, `Task`
- FastAPI `ai_server/` — mock + optional HF loaders
- Celery tasks: `transform_prompt`, `embed_prompt`
- APIs: transform, task status, agent JSON, similar, `me/transformations/`
- UI: inline transform on detail, library tab “내 변환”, `prompt_type` on form
- WebSocket `ws/tasks/?token=` + polling fallback

### What this week must prove

End-to-end flow from the self-check checklist:

> User input → Django → DB → AI request → **async (Celery)** → result in DB → **inline UI** → **monitoring**

---

## Daily completion criteria (at a glance)

| Date | WBS day | One-line “done” |
|------|---------|-----------------|
| **06-02** | Day 2 | Migrations applied; 4th models visible in Admin; Phase 3 features still work |
| **06-03** | Day 3 | `:8001/health` OK; FastAPI `/docs` transform (mock) OK |
| **06-04** | Day 4 | `celery_worker` healthy; Task PENDING → SUCCESS (or FAIL with message) |
| **06-05** | Day 5 | Author transform → inline 4 steps + library “내 변환” tab |
| **06-06** | Day 6 | Prometheus targets UP; Grafana screenshots |
| **06-07** | Day 7 | WebSocket + polling fallback; full stack restart demo passes |
| **06-08** | Day 8 | Live presentation + evidence package submitted |

---

## Common commands (EC2)

Run from the project root on EC2 after `git pull`:

```bash
# Start / rebuild stack
docker compose up -d --build

# Migrations (after schema changes)
docker compose exec web python manage.py migrate --noinput

# Optional sample data
docker compose exec web python manage.py seed_mockup

# Status & logs
docker compose ps
docker compose logs celery_worker --tail 50
docker compose logs ai_server --tail 50

# Health checks
curl -s http://127.0.0.1:8001/health
curl -fsS http://127.0.0.1:8000/
```

**Environment (recommended for rehearsal):**

```bash
# .env on EC2
LLM_PROVIDER=mock
FASTAPI_URL=http://ai_server:8000
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

**Security groups:** open **8000**, **8001**, **9090**, **3000** (or use SSH tunnels for demo).

---

## June 2 (Tue) — Day 2 · Data model

**WBS goal:** Extend domain schema, AI result tables, Task model, Admin, migrations, seed.

### Tasks

| # | Task | Notes |
|---|------|-------|
| 1 | Deploy latest `main` on EC2 | `git pull` → `docker compose up -d --build` |
| 2 | Run migrations | `docker compose exec web python manage.py migrate --noinput` |
| 3 | Verify tables in Admin | `AgentTransformation`, `PromptEmbedding`, `Task`; Prompt has `prompt_type`, `workflow_steps`, `agent_pattern` |
| 4 | Seed data | `seed_mockup` — add **3× `agent_recipe`** examples if not yet in seed |
| 5 | ERD evidence | Export from [DATA_MODEL_BY_PHASE.md](./DATA_MODEL_BY_PHASE.md) (mermaid.live → PNG) |
| 6 | Phase 3 regression | Register/login, CRUD, comments, likes, bookmarks, search, pagination |

### Exit criteria

- You can explain: core models + how **AI results are separate tables** (no overwrite of `Prompt.content`).
- Self-check §2 (3차 유지), §3 (데이터 구조) partially satisfied.

### Evidence to capture

- [ ] Admin screenshot: Task + AgentTransformation list
- [ ] ERD image for slide deck

---

## June 3 (Wed) — Day 3 · FastAPI + AI server

**WBS goal:** Independent AI server, mock/HF, `/health`, `/transform`, `/embed`.

### Tasks

| # | Task | Notes |
|---|------|-------|
| 1 | Container health | `docker compose ps` — `ai_server` healthy |
| 2 | Health endpoint | `curl http://<EC2>:8001/health` → `ok`, `provider: mock` |
| 3 | FastAPI docs | Open `http://<EC2>:8001/docs` |
| 4 | Manual transform | POST `/transform` with sample `prompt_text` → 4-step JSON |
| 5 | Lock mock for rehearsal | `LLM_PROVIDER=mock` in EC2 `.env` (DECISIONS Q10) |
| 6 | HF prep (optional) | Extend `ai_server` image with torch/transformers; first run 10–15 min download — not required for daily rehearsal |

### Exit criteria

- Clear story: **Django does not run the model**; FastAPI does.
- Self-check §4-2, §4-3 (FastAPI 분리, 엔드포인트 설명).

### Evidence to capture

- [ ] `/docs` screenshot
- [ ] Sample `/transform` response (JSON or UI from Swagger)

---

## June 4 (Thu) — Day 4 · Celery + Redis

**WBS goal:** Async worker, Task state machine, Django → FastAPI via httpx.

### Tasks

| # | Task | Notes |
|---|------|-------|
| 1 | Redis | `docker compose exec redis redis-cli ping` → `PONG` |
| 2 | Celery worker | `docker compose logs celery_worker` — `ready` |
| 3 | Task lifecycle | Trigger transform (shell or next-day UI); confirm PENDING → PROCESSING → SUCCESS in Admin |
| 4 | Failure path | Optional: stop `ai_server` briefly → Task FAIL + `error_message` |
| 5 | Embed on create | New prompt → `Task` with `task_type=embed` (skipped during `manage.py test`) |

### Exit criteria

- Immediate **202 + task_id**; long work off the HTTP thread.
- Self-check §5-1 ~ §5-3 (Celery + Redis, Task 생성, 상태 4단계).

### Evidence to capture

- [ ] Celery worker log line: `transform_success` or equivalent
- [ ] Admin: Task row with SUCCESS and `result_id`

---

## June 5 (Fri) — Day 5 · API + UI (core demo path)

**WBS goal:** Transform API, status polling, **inline** agent UI on detail, library tab.

### Tasks

| # | Task | Notes |
|---|------|-------|
| 1 | Login as **author** | Non-author must not see transform button (Q7) |
| 2 | Detail page | Open own prompt → **에이전트로 변환하기** |
| 3 | UX | “변환 중… N초” → mock ~2–3s → **4 steps + confidence** inline |
| 4 | Network tab | `POST .../transform/` → `GET .../tasks/{id}/status/` → `GET .../agent/` |
| 5 | Library | Tab **내 변환** — latest transform per owned prompt (Q3) |
| 6 | Similar prompts | After embed SUCCESS on 2+ prompts, check similar list on detail |
| 7 | Full script once | Home → explore → login → transform → library (record or checklist) |

### Exit criteria

- Full user story for presentation sections (2) AI 연결 + (3) 비동기.
- Self-check §4-4, §5-4, §5-5 (결과 저장/조회, 화면, 상태 API).

### Evidence to capture

- [ ] Detail page with inline agent steps
- [ ] Library “내 변환” tab
- [ ] DevTools: task status JSON

---

## June 6 (Sat) — Day 6 · Monitoring + similarity

**WBS goal:** Prometheus, Grafana, `/metrics`, embedding similarity.

### Tasks

| # | Task | Notes |
|---|------|-------|
| 1 | Prometheus | `http://<EC2>:9090/targets` — jobs `django`, `fastapi` **UP** |
| 2 | Django metrics | `http://<EC2>:8000/metrics` loads |
| 3 | Grafana | `http://<EC2>:3000` (admin/admin); Prometheus datasource |
| 4 | Dashboard | Panels: traffic, latency, task outcomes; run 2–3 transforms to populate graphs |
| 5 | Similarity | `GET /api/prompts/{id}/similar/` after embeddings exist |
| 6 | Self-check §7–10 | Mark `[x]` only for items you can demo live |

### Exit criteria

- Presentation section (5) 모니터링 + 배포 구조.
- Bonus rubric: Prometheus + Grafana + custom metrics.

### Evidence to capture

- [ ] Prometheus targets UP
- [ ] Grafana dashboard screenshot
- [ ] (Optional) `agent_transformation_total` or inference histogram visible

---

## June 7 (Sun) — Day 7 · WebSocket + stabilization

**WBS goal:** WS task updates, polling fallback, troubleshooting doc, full restart rehearsal.

### Tasks

| # | Task | Notes |
|---|------|-------|
| 1 | WebSocket | On transform, DevTools → `ws/tasks/?token=...`; UI hint “실시간 알림 연결됨” |
| 2 | Fallback | Disable WS or block WS port → polling still reaches SUCCESS (Q11) |
| 3 | Troubleshooting | Create/update `docs/troubleshooting.md` — 3 scenarios (ai_server slow, Celery broker, Prometheus scrape) |
| 4 | Cold start | `docker compose down` → `up -d --build` → migrate → one full demo |
| 5 | Slides draft | 15 min outline per 발표 가이드 (intro, 3차, AI, async, ops, demo, limits) |
| 6 | Ports / SG | Finalize EC2 security group rules |

### Exit criteria

- Confident recovery narrative if something fails during demo.
- Self-check §5-5 (WS or polling), §7 (예외/로그).

### Evidence to capture

- [ ] WS connected in DevTools
- [ ] (Optional) FAIL task screenshot with `error_message` for slide “한계/대응”

---

## June 8 (Mon) — Day 8 · Demo + presentation

**WBS goal:** Live 21-step flow, 3 rehearsals, submission package.

### Suggested live flow (10–15 min)

| Step | Content | ~min |
|------|---------|------|
| 1 | Problem, users, 3차 → 4차 evolution | 1.5 |
| 2 | Architecture diagram (7 containers) | 1.5 |
| 3 | Phase 3 quick: browse, login | 1 |
| 4 | **Transform button** → Task → inline 4 steps | 3 |
| 5 | Library “내 변환” | 1 |
| 6 | FastAPI `/docs` + one `/transform` | 1 |
| 7 | Prometheus + Grafana | 2 |
| 8 | Admin: Task / AgentTransformation | 0.5 |
| 9 | Limits (mock default, no payment, no analyze MVP) + roadmap | 1 |

### Tasks

| # | Task | Notes |
|---|------|-------|
| 1 | Morning check | `LLM_PROVIDER=mock`, all containers healthy |
| 2 | Rehearsal ×3 | Same script; only claim what you showed |
| 3 | Evidence pack | See checklist below |
| 4 | HF (optional) | 30s “real model” only if HF image ready; main demo stays mock |

### Evidence submission checklist

- [ ] Main UI / transform result
- [ ] `docker compose ps` (7 services)
- [ ] FastAPI `/docs`
- [ ] Celery log or Task SUCCESS in Admin
- [ ] Prometheus targets UP
- [ ] Grafana dashboard
- [ ] (Optional) FAIL case + error_message
- [ ] GitHub / deploy URL on cover slide

### Exit criteria

- All items in **자가정검** that you marked `[x]` are demoable without improvisation.
- Evaluation: “AI + operations backend” story is complete.

---

## Mapping to evaluation rubric

| Rubric area | Primary days |
|-------------|--------------|
| 3차 서비스 유지 | 06-02, 06-05 |
| AI + server split | 06-03, 06-05 |
| AI result DB + API/UI | 06-02, 06-05 |
| Async (Celery + Redis) | 06-04, 06-05 |
| Task status 4단계 | 06-04, 06-05, 06-07 |
| Docker Compose | 06-02 ~ 06-07 |
| Monitoring | 06-06 |
| Deploy / reproducibility | 06-02, 06-07, 06-08 |

---

## Out of scope this week (per DECISIONS)

| Item | Reason |
|------|--------|
| `AnalysisResult` / analyze task | Q4 — MVP excluded |
| Payment for paid prompts | Business phase 3 |
| Dedicated `/prompts/{id}/agent/` page | Q2 — inline only |
| Vercel as primary 4th host | Q1 — EC2 Compose |
| `mcp_package` UI | Q8 — DB choice only, UI disabled |

---

## Priority if time is short

1. **06-02:** EC2 deploy + `migrate` + Phase 3 smoke test  
2. **06-05:** Full transform demo path (non-negotiable)  
3. **06-06:** Prometheus + Grafana screenshots  
4. **06-08:** Rehearsal + evidence  

Everything else strengthens the score but depends on (2) working on EC2.

---

## Document history

| Date | Note |
|------|------|
| 2026-05-27 | Initial schedule from WBS v2 + DECISIONS Q1–Q12 + repo implementation status |
