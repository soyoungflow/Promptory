# Promptory — 발표·과제 자가점검 (코드베이스 기준)

> **이 문서의 체크 규칙**  
> - `[x]` : 저장소 코드·설정·README 기준으로 **구현되어 있고**, 정상 실행 환경에서 **시연 가능**한 것으로 판단됨.  
> - `[ ]` : **저장소에 없음**, **발표 구성(대본·시간·슬라이드)** 등 코드 밖 준비, 또는 **발표 직전 직접 시연 확인**이 필요함.  
>  
> 실제 발표에서 `[x]`를 표시하려면 **반드시 직접 1회 이상 시연**해 주세요.

---

## 1. 프로젝트 소개 및 발표 구성

| 항목 | 권장 | 비고 |
|------|:----:|------|
| 프로젝트명과 한 줄 소개 | [ ] | README: **Promptory** — AI 프롬프트 공유·판매 서비스 (Django + DRF + JWT). 발표 대본은 팀이 작성. |
| 해결하려는 문제 | [ ] | 코드가 아닌 기획·발표 설명 영역. |
| 주요 사용자 | [ ] | 동상. |
| 발표 10분 내외 | [ ] | 리허설로 확인. |

---

## 2. 핵심 데이터 구조 설명

| 항목 | 권장 | 근거 (코드) |
|------|:----:|------------|
| 핵심 도메인 모델 설명 | [x] | 핵심은 `prompts.models.Prompt` (프롬프트 본문·가격·조회수·AI 모델·Soft Delete 등). |
| 연결 모델 1개 이상 | [x] | 예: `Category`, `Tag`(M2M), `PromptFile`, `interaction.Comment` / `Like` / `Bookmark`. |
| User ↔ 핵심 데이터 관계 | [x] | `Prompt.user` → `AUTH_USER_MODEL`; 댓글·좋아요·북마크도 `user` FK. |
| 설계 이유 설명 | [ ] | ERD·슬라이드에서 논리 정리 필요. 코드상: 카테고리/태그 분리, Soft Delete, 파일 메타데이터 분리 등. |
| ERD 발표 자료 포함 | [ ] | **저장소 내 ERD 파일 없음.** 슬라이드/문서에 별도 포함 필요. |

---

## 3. 백엔드 구조 설명

| 항목 | 권장 | 근거 |
|------|:----:|------|
| Model 역할 | [x] | `accounts`, `prompts`, `interaction` 앱의 `models.py`. |
| Serializer 역할 | [x] | DRF Serializer: 검증·입출력 필드 (`prompts/serializers.py`, `accounts/serializers.py` 등). |
| View 역할 | [x] | DRF `ViewSet`/`APIView`; 템플릿용 뷰는 별도 (`prompts/template_views.py` 등). |
| Template 역할 | [x] | `templates/` HTML + `static/js` — 화면 렌더링·폼 UI; 데이터는 API 호출. |
| Template vs DRF API 분리 | [x] | `config/urls.py`: `/api/...` DRF, `/`, `/accounts/`, `/prompts/...` 템플릿 라우트. README 「인증 정책」에 JWT-only 설명. |
| 앱 책임 분리 | [x] | `accounts`(회원·프로필), `prompts`(도메인), `interaction`(댓글·좋아요·북마크), `config`, `ai_gateway`(확장용). |
| static / js / template | [x] | `static/css`, `static/js/*`, `templates/` — README 앱 구조 표 참고. |

---

## 4. 필수 기능 자가점검

### 4-1. 회원가입

| 항목 | 권장 | 근거 |
|------|:----:|------|
| 회원가입 동작 | [x] | `POST /api/accounts/register/` — `RegisterView`, JWT 즉시 발급. |
| 필수값 누락 검증 | [x] | `RegisterSerializer` + Model 필드; `validate_password`, 비밀번호 일치 검증. |
| 중복 가입 차단 | [x] | `CustomUser.email` `unique=True`; DRF 저장 시 유효성 검증. |
| 비밀번호 해시 저장 | [x] | `User.objects.create_user()` → `set_password` 경로. |

### 4-2. 로그인 / 로그아웃

| 항목 | 권장 | 근거 |
|------|:----:|------|
| 로그인 동작 | [x] | SimpleJWT 로그인 엔드포인트(accounts URLs); 프론트 `login.js` + `auth.js` 토큰 저장. |
| 로그인 후 보호 기능 접근 | [x] | 예: 프롬프트 생성·수정·삭제·댓글 작성·좋아요는 `IsAuthenticated` 또는 객체 권한 필요. |
| 로그아웃 후 제한 | [x] | 토큰 제거 + `POST /api/accounts/logout/` 시 Refresh **블랙리스트** (`LogoutView`, `token_blacklist`). |

### 4-3. 핵심 도메인 CRUD (Prompt)

| 항목 | 권장 | 근거 |
|------|:----:|------|
| Create | [x] | `PromptViewSet`, `perform_create`에 작성자 지정. |
| Read | [x] | 목록/상세 API + 템플릿 목록/상세 페이지. |
| Update | [x] | `PUT`/`PATCH`, `IsAuthorOrReadOnly`. |
| Delete | [x] | `DELETE` → **Soft Delete** (`soft_delete`), 물리 삭제 아님. |
| 권한 규칙 (작성자만 수정/삭제) | [x] | `prompts/permissions.py` `IsAuthorOrReadOnly`. |

### 4-4. 분류 (카테고리 1단계)

| 항목 | 권장 | 근거 |
|------|:----:|------|
| 핵심 데이터 ↔ 카테고리 연결 | [x] | `Prompt.category` → `Category`. |
| 목록/상세에서 분류 표시 | [x] | API: `category_name` / `CategorySerializer`; UI 사이드바·필터. |

### 4-5. 검색

| 항목 | 권장 | 근거 |
|------|:----:|------|
| 단일 필드 검색 동작 | [x] | `?search=` — `PromptViewSet.search_fields = ['title', 'description']`. |
| 검색어에 따라 결과 변화 | [x] | DRF `SearchFilter`. 네비 검색은 `/prompts/?search=...` GET. |

### 4-6. 페이지네이션

| 항목 | 권장 | 근거 |
|------|:----:|------|
| 페이지 이동 | [x] | API: `PageNumberPagination`, `PAGE_SIZE=12`, `?page=`; 목록 페이지 JS에서 페이지 버튼 처리. |
| API/화면에서 확인 | [x] | 응답에 `count`, `next`, `previous` 등 (DRF 기본). |

### 4-7. 관리자 페이지

| 항목 | 권장 | 근거 |
|------|:----:|------|
| 관리자 로그인 | [ ] | **코드는 준비됨.** DB에 `is_staff`/`is_superuser` 계정이 없으면 로그인 불가 → 발표 전 `createsuperuser` 필수. |
| 핵심 데이터 관리 | [x] | `prompts/admin.py`: Prompt/Category/Tag/PromptFile, Soft Delete 액션·인라인 등. `interaction`, `accounts` admin 등록됨. |
| CRUD 확인 | [x] | Admin에서 생성·조회·수정 가능; Prompt 삭제는 운영 정책상 Soft Delete 권장(README 안내). |

### 4-8. 확장 기능 1종 이상

| 항목 | 권장 | 근거 |
|------|:----:|------|
| 확장 기능 동작 | [x] | **다수 구현**: 댓글(대댓글 구조), 좋아요 토글, 북마크, 파일 업로드(형식·용량 검증), 태그. |
| 발표 시 시연 | [ ] | 팀이 1~2개를 정해 **직접 시연**할 것. |

**선택 확장 기능 (코드 기준)**

- [x] 댓글 (`interaction`, `parent`로 대댓글)
- [x] 좋아요 (`LikeToggleView`, `unique_together`)
- [x] 북마크
- [ ] 「저장」 별도 도메인 없음 → 북마크로 시연 가능
- [ ] 상태 변경 — Prompt는 Soft Delete·가격 등으로 일부 해당; 별도 워크플로 state 필드는 없음
- [ ] 이미지 — 아바타 필드는 있으나 프롬프트 첨부는 **파일** 정책(jpg/png 등)
- [x] 파일 업로드 (`PromptFileSerializer` 확장자·10MB, `POST .../files/`)

**기타 (발표에서 구체화)**

- [ ] 태그 — 코드상 Tag + M2M으로 **태그 기능 구현됨**. 위 표에 없어서 여기 명시.

---

## 5. 데이터 흐름 완성도

| 항목 | 권장 | 비고 |
|------|:----:|------|
| 입력 → 서버 → DB → 출력 | [x] | 템플릿 페이지가 JS로 API 호출 후 화면 갱신 구조. |
| DB 반영 | [x] | 동일. |
| 저장 데이터 재표시 | [x] | 목록/상세 API·템플릿 재조회. |
| 핵심 시연 1회 점검 | [ ] | 발표 전 **전 구간 리허설** 권장. |

---

## 6. 관리자 및 권한 처리

| 항목 | 권장 | 비고 |
|------|:----:|------|
| 관리자 계정 준비 | [ ] | README에 `createsuperuser` 안내 있음. **실제 계정은 각 환경에서 생성.** |
| 관리자에서 핵심 데이터 관리 | [x] | `PromptAdmin` 등. |
| 일반 vs 관리자 차이 설명 | [x] | Django Admin vs JWT API `IsAuthenticated` / 객체 단위 권한. |
| 작성자/권한 기반 접근 제어 | [x] | 프롬프트 수정·삭제·댓글 삭제 등 코드상 구현. |

---

## 7. 산출물 준비 상태

| 항목 | 권장 | 비고 |
|------|:----:|------|
| ERD | [ ] | 저장소에 전용 파일 없음 → **발표 자료에 추가.** |
| 아키텍처 구조도 | [ ] | 동상. README의 앱·URL 분리 설명을 슬라이드로 옮기면 충족 가능. |
| API 명세 | [x] | README 「주요 API」「검색 파라미터」「API 응답 계약」. |
| 실행 방법 (README) | [x] | 로컬 실행, PostgreSQL 전환 절차, 테스트 명령. |
| 관리자 생성 방법 문서화 | [x] | README `createsuperuser`, `/admin/` URL. |

---

## 8. 실행 가능성 / 안정성

| 항목 | 권장 | 비고 |
|------|:----:|------|
| README만으로 실행 | [x] | venv, `pip install`, `.env.example` 복사, migrate, runserver. |
| 실행 순서 문서화 | [x] | README 순서. |
| 환경변수 문서화 | [x] | `.env.example` + README. |
| 발표 시 500 없음 | [ ] | 발표 직전 **로컬/배포 환경에서 재확인.** |
| 최종 점검 완료 | [ ] | 팀 실시. |

---

## 9. 선택 기능 가산점 (구현+시연+설명 시에만 [x])

아래는 **코드에 있는 기능** 기준 요약. 발표에서 가산점을 노리면 해당 항목을 **시연·설명**할 것.

| 항목 | 권장 | 근거 |
|------|:----:|------|
| JWT (Access 흐름) | [x] | SimpleJWT, Bearer 헤더. |
| JWT 고도화 (Refresh·재발급·블랙리스트) | [x] | `SIMPLE_JWT` ROTATE/`BLACKLIST_AFTER_ROTATION`, `logout` 블랙리스트, `auth.js` 갱신 패턴. |
| 파일 업로드 고도화 | [x] | 확장자·MIME·10MB, 메타 `file_name`/`file_type`/`file_size`. |
| 댓글 고도화 (대댓글 등) | [x] | `Comment.parent`, `ReplySerializer` 중첩; 삭제는 작성자만. |
| 인터렉션 고도화 | [x] | 좋아요 토글·`unique_together`, 카운트 응답. |
| 태그 | [x] | `Tag`, M2M, `tag_ids`/`tag_names` 작성 serializer. |
| 검색 고도화 | [x] | `search` + `django-filter` (`category`, `ai_model`, `is_free`, `tag`, `ordering`). |
| 페이지네이션 | [x] | PageNumber, page size 12. |
| 관리자 커스터마이징 | [x] | Prompt admin 액션·배지·인라인 등. |
| Soft Delete | [x] | Prompt·Comment; User 모델에도 `is_deleted` 필드. |
| 권한 고도화 | [x] | 객체 권한 + 인증 조합; 블랙리스트 로그아웃. |
| PostgreSQL 전환 | [x] | 로컬 `local.py`·운영 `production.py` 모두 PostgreSQL. Postgres 실행 후 마이그레이션·시연 확인. |
| 예외/에러 응답 표준화 | [ ] | DRF 기본 JSON 에러; 전역 커스텀 핸들러는 README에 명시 없음. |

---

## 10. 발표 직전 최종 확인

| 항목 | 권장 |
|------|:----:|
| 발표 자료 열림 | [ ] |
| 시연용·관리자 계정 준비 | [ ] |
| 테스트 데이터 | [ ] (예: `seed_mockup` 등) |
| 핵심 기능 1회 재점검 | [ ] |
| 네트워크·서버·실행 환경 | [ ] |

---

## 자가점검 결과 (팀이 직접 기입)

- **프로젝트명:** Promptory  
- **발표자:** __________________  
- **최종 자가점검일:** __________________  

### 필수 항목 점검 결과 (팀 판단)

- [ ] 발표 가능  
- [ ] 일부 보완 필요  
- [ ] 발표 전 수정 필요  

### 발표에서 반드시 보여줄 핵심 기능 (예시 — 팀에서 확정)

1. 회원가입/로그인 후 JWT로 프롬프트 등록·목록·상세  
2. 카테고리/검색/필터·페이지네이션  
3. 댓글 또는 좋아요·북마크·파일 첨부 중 1~2가지  

### 발표 전 마지막 점검 (자유 기입)

1. __________________  
2. __________________  
3. __________________  

---

## 코드 레퍼런스 빠른 목록

| 영역 | 경로 |
|------|------|
| URL 분리 | `config/urls.py` |
| JWT·DRF | `config/settings/base.py` (`SIMPLE_JWT`, `REST_FRAMEWORK`) |
| Prompt CRUD·검색·필터 | `prompts/views.py`, `prompts/filters.py` |
| 권한 | `prompts/permissions.py` |
| 회원가입·로그아웃 | `accounts/views.py` |
| 댓글·좋아요·북마크 | `interaction/views.py` |
| 파일 검증 | `prompts/serializers.py` `PromptFileSerializer` |
| Admin | `prompts/admin.py`, `interaction/admin.py`, `accounts/admin.py` |
