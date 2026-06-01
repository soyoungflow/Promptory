# Phase 3 — Implemented (Bootcamp “3차”)

**Status:** Complete in repository  
**Product slice:** Korean AI prompt **sharing** platform (discover, publish, engage).  
**Not in scope:** Agent auto-transformation, Celery, FastAPI, embeddings, operational metrics stack.

---

## 1. Goals and success criteria (achieved)

| Goal | Evidence |
|------|----------|
| Users can sign up and use JWT end-to-end | `accounts` register/login/logout/refresh APIs + `auth.js` |
| Prompt lifecycle with author permissions | `PromptViewSet` + `IsAuthorOrReadOnly` + soft delete |
| Discovery | Search, filters, pagination on `GET /api/prompts/` |
| Social loop | Comments (threaded), likes, bookmarks |
| Personal hub | `/library/` with 4 tabs (see Phase 4 gap: 5th tab planned) |
| Ops baseline | Docker Compose (web + Postgres), GitHub CI, EC2 CD |

---

## 2. Architecture (as built)

```
Browser
  ├─ GET /*           → Django TemplateView (HTML shell)
  └─ fetch /api/*     → DRF + JWT (data + permissions)

PostgreSQL ← Django ORM
Media files ← filesystem (MEDIA_ROOT)
```

| Layer | Responsibility |
|-------|----------------|
| Templates | Render pages only; no server-side business data |
| `static/js/*.js` | Call API, DOM updates, JWT in `localStorage` |
| DRF | Validation, permissions, serializers, DB |
| Admin | Session-based Django admin (separate from JWT UI) |

**Auth:** JWT-only for the SPA-style front end (`README.md` policy).  
**Settings:** `config.settings.local` (dev), `production`, `docker` (Compose).

---

## 3. User flows (summary)

Detailed English flows: [../USERFLOW.md](../USERFLOW.md).

| Flow | Entry | Key API |
|------|-------|---------|
| Register | `/accounts/register/` | `POST /api/accounts/register/` → tokens |
| Login | `/accounts/login/` | `POST /api/accounts/login/` |
| Explore | `/prompts/` | `GET /api/prompts/?search=&category=&...` |
| Detail | `/prompts/{id}/` | `GET /api/prompts/{id}/` (+ view_count++) |
| Create / edit | `/prompts/new/`, `.../edit/` | `POST` / `PUT /api/prompts/` |
| Like / bookmark | Detail actions | `POST .../like/`, `.../bookmark/` |
| Comments | Detail section | `GET/POST .../comments/`, `DELETE /api/comments/{id}/` |
| Library | `/library/` | `me/bookmarks`, `me/likes`, `me/prompts`, `me/comments` |
| Logout | Nav | `POST /api/accounts/logout/` + clear storage |

**Paid prompts:** `is_free=false` shows client-side preview only; **no payment API** (deferred to business Phase 3 in tech spec).

---

## 4. Routes and screens

| Screen | URL | JS |
|--------|-----|-----|
| Home | `/` | — |
| Explore | `/prompts/` | `prompts.js` |
| Detail | `/prompts/{id}/` | `prompt-detail.js` |
| Form | `/prompts/new/`, `/prompts/{id}/edit/` | `prompt-form.js` |
| Library | `/library/` | `library.js` |
| Login / Register | `/accounts/login/`, `register/` | `login.js`, `register.js` |
| Admin | `/admin/` | — |

---

## 5. API surface (Phase 3)

### Accounts (`/api/accounts/`)

| Method | Path | Notes |
|--------|------|-------|
| POST | `register/` | Returns access + refresh |
| POST | `login/` | SimpleJWT pair |
| POST | `logout/` | Refresh blacklist |
| POST | `token/refresh/` | Access renewal |
| GET/PATCH | `me/` | Profile (no dedicated UI page) |
| GET | `me/prompts/` | Author’s prompts |
| GET | `me/bookmarks/` | Bookmarked prompts |
| GET | `me/likes/` | Liked prompts |
| GET | `me/comments/` | User’s comments |

### Prompts (`/api/prompts/`)

| Method | Path | Notes |
|--------|------|-------|
| GET/POST | `/` | List / create |
| GET/PUT/PATCH/DELETE | `{id}/` | Detail / update / soft delete |
| POST | `{id}/files/` | Attachment upload |
| GET | `categories/`, `tags/` | Taxonomy (read-only viewsets) |

### Interaction (`/api/`)

| Method | Path |
|--------|------|
| GET/POST | `prompts/{id}/comments/` |
| DELETE | `comments/{id}/` |
| POST | `prompts/{id}/like/` |
| POST | `prompts/{id}/bookmark/` |

---

## 6. Data model (Phase 3 entities)

Implemented in code (see [DATA_MODEL_BY_PHASE.md](./DATA_MODEL_BY_PHASE.md) for field-level detail).

| Model | App | Notes |
|-------|-----|-------|
| `CustomUser` | accounts | `email` login; `is_deleted` soft delete |
| `Prompt` | prompts | `content` (not `body`); `ai_model`, pricing, soft delete |
| `Category`, `Tag` | prompts | Vendor-style categories |
| `PromptFile` | prompts | Attachments with validation |
| `Comment` | interaction | `parent` for replies |
| `Like`, `Bookmark` | interaction | Unique (user, prompt) |

**Stub:** `ai_gateway` app registered in `INSTALLED_APPS` but **no models or views** yet.

---

## 7. Infrastructure (Phase 3)

| Component | Implementation |
|-----------|----------------|
| Database | PostgreSQL (`config.settings.local` / `docker` / `production`) |
| Local run | `manage.py runserver` + `.env` |
| Docker | `docker-compose.yml`: **2 services** — `db`, `web` |
| CI | `.github/workflows/ci.yml` — check, migrate, test |
| CD | `.github/workflows/cd.yml` — SSH to EC2, `docker compose up` |
| Vercel | Optional Django deploy (settings auto-switch on `VERCEL=1`); **not** the 7-service Phase 4 stack |

---

## 8. Tests and quality

- `python manage.py test` — accounts, prompts, interaction contracts (JWT, soft delete, tags, etc.)
- Documented in `README.md` and `docs/STAGE3_GAP_ANALYSIS_AND_DELIVERABLES.md`

---

## 9. Known limitations (intentional for Phase 3)

| Item | Notes |
|------|-------|
| No AI transformation | `ai_gateway` empty |
| No async task queue | No Celery/Redis in `requirements.txt` |
| No similarity search | No `PromptEmbedding` |
| No payment | Paid content UI gate only |
| Library | 4 tabs, not 5 (no “my transformations”) |
| Profile UI | API only (`/api/accounts/me/`) |
| Session not used for pages | By design (JWT-only) |

---

## 10. Handoff to Phase 4

Phase 3 must **keep working** while Phase 4 adds:

- `prompt_type`, `workflow_steps`, `agent_pattern` on `Prompt`
- `ai_gateway` models + APIs
- `tasks` app + Celery
- `ai_server` FastAPI service
- Compose services: redis, ai_server, celery_worker, prometheus, grafana

See [PHASE_4_PLANNED.md](./PHASE_4_PLANNED.md) and [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md).
