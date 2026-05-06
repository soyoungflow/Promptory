# Promptory

AI 프롬프트 공유·판매 서비스 — Django 4.2 + DRF + JWT + PostgreSQL

---

## 로컬 실행 방법 (15분 내 실행 가능)

### 1. 프로젝트 클론
```bash
git clone https://github.com/your-id/Promptory.git
cd Promptory
```

### 2. 가상환경 생성 및 패키지 설치
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. PostgreSQL 준비 (로컬)
개발·테스트 모두 **PostgreSQL**을 사용한다.

```bash
# 예: Ubuntu/WSL — 서버 실행 후 DB 생성
sudo service postgresql start   # 환경에 따라 다름
createdb promptory_db           # 또는 psql 안에서 CREATE DATABASE
```

`.env`의 `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`가 실제 인스턴스와 일치해야 한다.

### 4. 환경 변수 설정
```bash
cp .env.example .env
# .env 에 SECRET_KEY, DB_* 값 수정
```

### 5. 마이그레이션 및 슈퍼유저 생성
```bash
python manage.py migrate
python manage.py createsuperuser
# 이메일, 사용자명, 비밀번호 입력
```

### 6. 개발 서버 실행
```bash
python manage.py runserver
```

브라우저에서 `http://127.0.0.1:8000/` 접속. 로컬 개발·마이그레이션·테스트 시 PostgreSQL 서버가 실행 중이어야 한다.

**기존 `db.sqlite3`에서 PostgreSQL로 데이터 이전:**

1. Postgres에 `migrate`까지 완료한 뒤, SQLite 덤프용 설정으로 내보낸다.

```bash
DJANGO_SETTINGS_MODULE=config.settings.sqlite_legacy python manage.py dumpdata \
  --natural-foreign --natural-primary \
  --exclude auth.permission --exclude contenttypes --exclude sessions \
  --exclude admin.logentry --exclude token_blacklist \
  --indent 2 -o migration_export/sqlite_export.json
```

2. PostgreSQL 쪽 데이터를 비운 뒤(테이블·마이그레이션 스키마는 유지) 로드한다.

```bash
python manage.py flush --no-input
python manage.py loaddata migration_export/sqlite_export.json
python manage.py sqlsequencereset accounts admin auth prompts interaction token_blacklist | python manage.py dbshell
```

`migration_export/` 내용은 `.gitignore`로 커밋되지 않게 두었다. 덤프에는 비밀번호 해시 등이 포함되므로 공유하지 않는다.

---

## Docker Compose (웹 + PostgreSQL)

운영과 같은 **`production` DB 패턴**에 가깝게 띄울 때 사용한다. 설정 모듈은 `config.settings.docker`(HTTP 개발 시 쿠키·CSRF 완화).

**준비:** Docker Desktop / Docker Engine + Compose plugin.

```bash
# 프로젝트 루트에서 (호스트 8000 포트가 비어 있어야 함)
docker compose build
docker compose up
```

- 앱: `http://127.0.0.1:8000/`
- DB는 Compose 네트워크 안에서만 열려 있으며 호스트 포트로 Postgres를 노출하지 않는다.

관리 명령은 한 번 실행 후 종료할 때 `docker compose run --rm web …` 를 쓴다.

```bash
docker compose run --rm web python manage.py createsuperuser
docker compose run --rm web python manage.py seed_mockup    # 선택
docker compose run --rm web python manage.py test
```

`SECRET_KEY`는 Compose 파일 기본값 대신 프로젝트 루트 `.env`에 두면 `${SECRET_KEY}` 로 치환된다. 실 서버 배포용 이미지에는 **디폴트 시크릿을 두지 말 것.**

개발 시 코드 변경 반영: `docker-compose.yml` 의 `.:/app` 마운트로 호스트 소스가 컨테이너에 반영된다(`venv/`는 `.dockerignore`로 빌드 제외).

### 사용법 (요약)

```bash
# 1) 컨테이너 빌드 + 실행
docker compose build
docker compose up

# 2) 관리 계정 생성 (최초 1회)
docker compose run --rm web python manage.py createsuperuser

# 3) (선택) 샘플 데이터 시드
docker compose run --rm web python manage.py seed_mockup

# 4) 테스트
docker compose run --rm web python manage.py test
```

---

## 관리자 페이지

```
http://127.0.0.1:8000/admin/
```

- 관리자 계정으로 로그인
- User / Prompt / Comment / Like / Bookmark / Tag 관리 가능
- Prompt → `is_deleted` 필드로 Soft Delete 상태 확인
- Prompt → 액션: "선택 항목 Soft Delete" / "선택 항목 복구"

---

## 앱 구조

```
accounts/       # 회원가입, 로그인, JWT 인증
prompts/        # 핵심 도메인 (Prompt, Category, Tag, PromptFile)
interaction/    # 댓글, 좋아요, 북마크
ai_gateway/     # 4차 확장 준비 (AI 연동)
config/         # Django settings, urls, WSGI/ASGI
templates/      # HTML 화면 렌더링 전용
static/
  css/main.css  # 전체 스타일
  js/auth.js    # JWT 저장/갱신 + 공통 API 클라이언트
  js/           # 기능별 JS

Dockerfile, docker-compose.yml, config/settings/docker.py  # Compose(웹+Postgres)
```

---

## 인증 정책

이 프로젝트는 **JWT-only** 방식으로 동작한다.

- 로그인/회원가입 API가 `access`, `refresh` 토큰을 반환한다.
- 브라우저는 토큰을 `localStorage`에 저장하고, API 요청마다 `Authorization: Bearer <access>`를 붙인다.
- Access Token 만료 시 `refresh` 토큰으로 자동 재발급한다.
- Django Template View는 화면만 렌더링하며, 세션 로그인 여부로 페이지 접근을 막지 않는다.
- 실제 권한 검사는 DRF permission과 JWT 인증이 담당한다.

공통 JS 클라이언트는 `static/js/auth.js`의 `Auth`, `Api` 객체를 사용한다.

---

## 주요 API

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| POST | /api/accounts/register/ | 회원가입 |
| POST | /api/accounts/login/ | 로그인 (JWT) |
| POST | /api/accounts/logout/ | 로그아웃 |
| GET  | /api/accounts/me/bookmarks/ | 내 북마크 프롬프트 목록 |
| GET  | /api/accounts/me/likes/ | 좋아요한 프롬프트 목록 |
| GET  | /api/accounts/me/prompts/ | 내가 등록한 프롬프트 목록 |
| GET  | /api/accounts/me/comments/ | 내가 쓴 댓글 목록 (프롬프트 제목 포함) |
| GET  | /api/prompts/ | 목록 (검색/필터/페이지네이션) |
| POST | /api/prompts/ | 프롬프트 등록 |
| GET  | /api/prompts/{id}/ | 상세 |
| PUT  | /api/prompts/{id}/ | 수정 (작성자만) |
| DELETE | /api/prompts/{id}/ | Soft Delete |
| POST | /api/prompts/{id}/like/ | 좋아요 토글 |
| POST | /api/prompts/{id}/bookmark/ | 북마크 토글 |
| GET/POST | /api/prompts/{id}/comments/ | 댓글 목록/작성 |

---

## API 응답 계약

프론트엔드가 권한과 UI 상태를 안정적으로 판단할 수 있도록 다음 필드를 명시적으로 제공한다.

- Prompt 목록/상세: `user_id`, `author`, `like_count`, `bookmark_count`, `is_liked`, `is_bookmarked`
- Prompt 상세: `comment_count`, `category`, `tags`, `files`
- Prompt 생성/수정 응답: `id`
- Comment/Reply: `user_id`, `author`, `content`, `is_deleted`
- Prompt 생성/수정 입력: 기존 태그는 `tag_ids`, 새 태그는 `tag_names`

파일 업로드는 `multipart/form-data`로 전송하며, `Api.upload()`를 사용한다.

---

## 검색 파라미터

```
GET /api/prompts/
  ?search=키워드          # title, description 검색
  ?category=1             # 카테고리 ID
  ?ai_model=gpt-5-5       # AI 모델
  ?is_free=true           # 무료 여부
  ?tag=python             # 태그 슬러그
  ?ordering=-created_at   # 정렬 (최신순 기본)
  ?page=2                 # 페이지 (기본 12개, 최대 50개)
```

---

## 운영 설정 (`production`)

로컬 기본은 `config.settings.local`(PostgreSQL + DEBUG=True). 서버 배포 시:

```bash
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py migrate
```

`.env`에 `DEBUG=False`, `ALLOWED_HOSTS`, 동일한 `DB_*`(또는 운영 DB)를 맞춘다.

---

## 테스트

PostgreSQL이 실행 중이어야 한다 (`manage.py test`는 테스트용 DB를 생성한다).

가상환경을 활성화한 뒤 실행한다 (`venv`에 Django가 설치됨).

```bash
source venv/bin/activate          # Windows: venv\Scripts\activate
python manage.py check
python manage.py test
```



활성화 없이 시스템 `python`만 쓰면 Django가 없어 `ModuleNotFoundError` / `Couldn't import Django` 가 난다. 그때는 `./venv/bin/python manage.py test` 로 실행하면 된다.

현재 테스트 범위:

- 회원가입 JWT 응답 계약
- JWT 기반 내 프로필 API
- JWT-only 템플릿 접근
- 프롬프트 생성/상세/권한 계약
- 기존 태그와 새 태그 동시 처리
- 댓글 `user_id` 응답 계약
- 좋아요/북마크 토글
- 댓글 soft delete

---

## 기술 스택

- **Backend**: Python 3.11, Django 4.2, DRF 3.15
- **인증**: djangorestframework-simplejwt (Access 60분, Refresh 7일)
- **필터**: django-filter
- **DB**: PostgreSQL (로컬 `local.py`, 운영 `production.py`)
- **Frontend**: Django Template + Vanilla JS (인라인 JS 없음)
