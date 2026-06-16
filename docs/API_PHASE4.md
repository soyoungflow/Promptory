# Phase 4 API 명세 (AI · 비동기 · 설계서)

3차 CRUD API는 [README.md](../README.md) 「주요 API」 참고.  
FastAPI 스키마는 배포 환경 `http://<HOST>/ai/docs` (Swagger).

---

## 인증

대부분 `Authorization: Bearer <access_token>` 필요.  
예외: `GET /api/prompts/` 목록·상세(일부), `GET /ai/health`.

---

## 설계서 만들기 (BlueprintDesign)

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/blueprints/design/` | 설계서 생성 + Celery 변환 Task 큐잉 |
| GET | `/api/blueprints/design/` | 내 설계서 목록 |
| GET | `/api/blueprints/design/{id}/` | 설계서 상세 |
| POST | `/api/blueprints/design/{id}/publish-recipe/` | 완료 설계서를 레시피 초안으로 등록 |

### POST `/api/blueprints/design/` 요청 예시

```json
{
  "brief": "주간 보고서를 자동으로 요약하고 슬랙에 올리고 싶어요",
  "extra_context": "팀 5명, 매주 금요일",
  "title": "주간 보고 자동화"
}
```

### 응답 예시 (202)

```json
{
  "id": 1,
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status_url": "/api/tasks/a1b2c3d4-e5f6-7890-abcd-ef1234567890/status/",
  "status": "pending"
}
```

---

## 프롬프트 변환 (레거시·API 직접 호출)

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/prompts/{id}/transform/` | 작성자 프롬프트 → Celery 변환 (Task 반환) |
| GET | `/api/prompts/{id}/agent/` | 최신 AgentTransformation JSON |
| GET | `/api/prompts/{id}/similar/` | 유사 레시피 (임베딩·mock) |

---

## Task 상태

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/tasks/{task_id}/status/` | PENDING / PROCESSING / SUCCESS / FAIL |

### 응답 예시 (SUCCESS)

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "SUCCESS",
  "task_type": "transform",
  "error_message": "",
  "result_id": 12,
  "has_result": true
}
```

### 실패 예시 (FAIL)

```json
{
  "status": "FAIL",
  "error_message": "FastAPI transform failed: connection refused"
}
```

---

## 보관함

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/accounts/me/transformations/` | 내 변환 이력 (프롬프트당 최신 1건) |

---

## FastAPI (ai_server)

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/health` | `ok`, `provider` |
| POST | `/transform` | 4단계 에이전트 JSON (mock/HF) |
| POST | `/embed` | 텍스트 임베딩 벡터 |

프록시 경로: `/ai/health`, `/ai/docs`, `/ai/transform` 등 ([NGINX_REVERSE_PROXY.md](./NGINX_REVERSE_PROXY.md)).

---

## WebSocket

```
ws://<HOST>/ws/tasks/?token=<access_token>
```

Task 상태 변경 시 WebSocket push 가능. **`blueprint-design.js`는 `GET /api/tasks/{task_id}/status/`를 폴링**하고, SUCCESS 시 `GET /api/blueprints/design/{id}/`로 최종 결과를 표시합니다.
