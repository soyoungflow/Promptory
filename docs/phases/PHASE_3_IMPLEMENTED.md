# Phase 3 — 구현 완료 (부트캠프 「3차」)

**상태:** 저장소에 구현 완료  
**제품 범위:** 한국어 AI 프롬프트 **공유** 플랫폼 (탐색, 게시, 참여).  
**범위 밖:** 에이전트 자동 변환, Celery, FastAPI, 임베딩, 운영 메트릭 스택 (Phase 4에서 추가).

---

## 1. 목표 및 달성 기준

| 목표 | 근거 |
|------|------|
| JWT로 가입부터 E2E 사용 | `accounts` register/login/logout/refresh API + `auth.js` |
| 작성자 권한으로 프롬프트 생명주기 | `PromptViewSet` + `IsAuthorOrReadOnly` + soft delete |
| 탐색 | `GET /api/prompts/` 검색·필터·페이지네이션 |
| 소셜 루프 | 댓글(스레드), 좋아요, 북마크 |
| 개인 허브 | `/library/` 4탭 (5번째 「내 변환」은 Phase 4) |
| 운영 기본 | Docker Compose (web + Postgres), GitHub CI, EC2 CD |

---

## 2. 아키텍처 (구현 기준)

```
Browser
  ├─ GET /*           → Django TemplateView (HTML 껍데기)
  └─ fetch /api/*     → DRF + JWT (데이터 + 권한)

PostgreSQL ← Django ORM
Media files ← filesystem (MEDIA_ROOT)
```

| 계층 | 역할 |
|------|------|
| Templates | 페이지 렌더만; 서버 사이드 비즈니스 데이터 없음 |
| `static/js/*.js` | API 호출, DOM 갱신, JWT `localStorage` |
| DRF | 검증, 권한, serializer, DB |
| Admin | 세션 기반 Django admin (JWT UI와 분리) |

**인증:** SPA형 프론트는 JWT 전용 (`README.md` 정책).  
**설정:** `config.settings.local` (개발), `production`, `docker` (Compose).

---

## 3. 사용자 흐름 (요약)

| 흐름 | 진입 | 주요 API |
|------|------|----------|
| 회원가입 | `/accounts/register/` | `POST /api/accounts/register/` → tokens |
| 로그인 | `/accounts/login/` | `POST /api/accounts/login/` |
| 탐색 | `/prompts/` | `GET /api/prompts/?search=&category=&...` |
| 상세 | `/prompts/{id}/` | `GET /api/prompts/{id}/` (+ view_count++) |
| 작성/수정 | `/prompts/new/`, `.../edit/` | `POST` / `PUT /api/prompts/` |
| 좋아요/북마크 | 상세 액션 | `POST .../like/`, `.../bookmark/` |
| 댓글 | 상세 섹션 | `GET/POST .../comments/`, `DELETE /api/comments/{id}/` |
| 보관함 | `/library/` | `me/bookmarks`, `me/likes`, `me/prompts`, `me/comments` |
| 로그아웃 | Nav | `POST /api/accounts/logout/` + storage 비우기 |

**유료 프롬프트:** `is_free=false`는 클라이언트 미리보기만; **결제 API 없음** (기술문서 비즈니스 Phase 3로 이연).

---

## 4. 라우트 및 화면

| 화면 | URL | JS |
|------|-----|-----|
| 홈 | `/` | — |
| 탐색 | `/prompts/` | `prompts.js` |
| 상세 | `/prompts/{id}/` | `prompt-detail.js` |
| 폼 | `/prompts/new/`, `/prompts/{id}/edit/` | `prompt-form.js` |
| 보관함 | `/library/` | `library.js` |
| 로그인/가입 | `/accounts/login/`, `register/` | `login.js`, `register.js` |
| Admin | `/admin/` | — |

---

## 5. API 표면 (Phase 3)

### Accounts (`/api/accounts/`)

| Method | Path | 비고 |
|--------|------|------|
| POST | `register/` | access + refresh 반환 |
| POST | `login/` | SimpleJWT pair |
| POST | `logout/` | Refresh blacklist |
| POST | `token/refresh/` | Access 갱신 |
| GET/PATCH | `me/` | 프로필 (전용 UI 페이지 없음) |
| GET | `me/prompts/` | 작성자 프롬프트 |
| GET | `me/bookmarks/` | 북마크한 프롬프트 |
| GET | `me/likes/` | 좋아요한 프롬프트 |
| GET | `me/comments/` | 사용자 댓글 |

### Prompts (`/api/prompts/`)

| Method | Path | 비고 |
|--------|------|------|
| GET/POST | `/` | 목록 / 생성 |
| GET/PUT/PATCH/DELETE | `{id}/` | 상세 / 수정 / soft delete |
| POST | `{id}/files/` | 첨부 업로드 |
| GET | `categories/`, `tags/` | 분류 (read-only viewsets) |

### Interaction (`/api/`)

| Method | Path |
|--------|------|
| GET/POST | `prompts/{id}/comments/` |
| DELETE | `comments/{id}/` |
| POST | `prompts/{id}/like/` |
| POST | `prompts/{id}/bookmark/` |

---

## 6. 데이터 모델 (Phase 3 엔티티)

코드 기준 구현 (필드 상세는 [DATA_MODEL_BY_PHASE.md](./DATA_MODEL_BY_PHASE.md)).

| Model | App | 비고 |
|-------|-----|------|
| `CustomUser` | accounts | `email` 로그인; `is_deleted` soft delete |
| `Prompt` | prompts | `content` (`body` 아님); `ai_model`, 가격, soft delete |
| `Category`, `Tag` | prompts | 벤더 스타일 카테고리 |
| `PromptFile` | prompts | 검증 포함 첨부 |
| `Comment` | interaction | `parent`로 대댓글 |
| `Like`, `Bookmark` | interaction | (user, prompt) 유니크 |

**Phase 4 이전:** `ai_gateway`는 `INSTALLED_APPS`에만 등록된 스텁이었음 → Phase 4에서 모델·뷰 추가.

---

## 7. 인프라 (Phase 3)

| 구성요소 | 구현 |
|----------|------|
| Database | PostgreSQL (`config.settings.local` / `docker` / `production`) |
| 로컬 실행 | `manage.py runserver` + `.env` |
| Docker | `docker-compose.yml`: **2서비스** — `db`, `web` (Phase 4에서 7서비스로 확장) |
| CI | `.github/workflows/ci.yml` — check, migrate, test |
| CD | `.github/workflows/cd.yml` — SSH EC2, `docker compose up` |
| Vercel | 선택 Django 배포 (`VERCEL=1` 시 production); **7서비스 Phase 4 스택 아님** |

---

## 8. 테스트 및 품질

- `python manage.py test` — accounts, prompts, interaction (JWT, soft delete, tags 등)
- 프로젝트 `README.md` 참고

---

## 9. 알려진 제한 (Phase 3 의도적 범위)

| 항목 | 비고 |
|------|------|
| AI 변환 없음 | Phase 4에서 `ai_gateway` 구현 |
| 비동기 큐 없음 | Phase 4에서 Celery/Redis |
| 유사도 검색 없음 | Phase 4에서 `PromptEmbedding` |
| 결제 없음 | 유료 UI 게이트만 |
| 보관함 4탭 | 「내 변환」은 Phase 4 |
| 프로필 UI | API만 (`/api/accounts/me/`) |
| 페이지에 세션 미사용 | JWT 전용 설계 |

---

## 10. Phase 4로의 인계

Phase 3 기능은 **유지**한 채 Phase 4가 추가합니다:

- `Prompt`에 `prompt_type`, `workflow_steps`, `agent_pattern`
- `ai_gateway` 모델 + API
- `tasks` 앱 + Celery
- `ai_server` FastAPI 서비스
- Compose: redis, ai_server, celery_worker, prometheus, grafana

[PHASE_4_PLANNED.md](./PHASE_4_PLANNED.md), [DECISIONS.md](./DECISIONS.md) 참고.
