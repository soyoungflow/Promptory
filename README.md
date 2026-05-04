# PromptHub

AI 프롬프트 공유·판매 서비스 — Django 4.2 + DRF + PostgreSQL

---

## 로컬 실행 방법 (15분 내 실행 가능)

### 1. 프로젝트 클론
```bash
git clone https://github.com/your-id/prompthub.git
cd prompthub
```

### 2. 가상환경 생성 및 패키지 설치
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 SECRET_KEY 등 필요한 값 수정
```

### 4. 마이그레이션 및 슈퍼유저 생성
```bash
python manage.py migrate
python manage.py createsuperuser
# 이메일, 사용자명, 비밀번호 입력
```

### 5. 개발 서버 실행
```bash
python manage.py runserver
```

브라우저에서 `http://127.0.0.1:8000/` 접속

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
templates/      # HTML 화면 렌더링 전용
static/
  css/main.css  # 전체 스타일
  js/           # 기능별 JS (인라인 JS 없음)
```

---

## 주요 API

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| POST | /api/accounts/register/ | 회원가입 |
| POST | /api/accounts/login/ | 로그인 (JWT) |
| POST | /api/accounts/logout/ | 로그아웃 |
| GET  | /api/prompts/ | 목록 (검색/필터/페이지네이션) |
| POST | /api/prompts/ | 프롬프트 등록 |
| GET  | /api/prompts/{id}/ | 상세 |
| PUT  | /api/prompts/{id}/ | 수정 (작성자만) |
| DELETE | /api/prompts/{id}/ | Soft Delete |
| POST | /api/prompts/{id}/like/ | 좋아요 토글 |
| POST | /api/prompts/{id}/bookmark/ | 북마크 토글 |
| GET/POST | /api/prompts/{id}/comments/ | 댓글 목록/작성 |

---

## 검색 파라미터

```
GET /api/prompts/
  ?search=키워드          # title, description 검색
  ?category=1             # 카테고리 ID
  ?ai_model=gpt-4o        # AI 모델
  ?is_free=true           # 무료 여부
  ?tag=python             # 태그 슬러그
  ?ordering=-created_at   # 정렬 (최신순 기본)
  ?page=2                 # 페이지 (기본 12개, 최대 50개)
```

---

## PostgreSQL 전환 (CRUD 완성 후)

```bash
# .env 수정
DB_ENGINE=django.db.backends.postgresql
DB_NAME=prompthub_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# settings/__init__.py 에서 production 설정으로 변경
# 마이그레이션 재실행
python manage.py migrate
```

---

## 기술 스택

- **Backend**: Python 3.11, Django 4.2, DRF 3.15
- **인증**: djangorestframework-simplejwt (Access 60분, Refresh 7일)
- **필터**: django-filter
- **DB**: SQLite (개발) → PostgreSQL (운영)
- **Frontend**: Django Template + Vanilla JS (인라인 JS 없음)
# Promptory
