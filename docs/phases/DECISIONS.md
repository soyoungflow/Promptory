# Phase 4 — 확정 결정 (2026-05-27)

구현에 고정된 항목입니다. 평가 참고: `docs/4차 발표가이드 및 평가기준.md`, `docs/자가정검 체크리스트(개인프로젝트).md`.

| ID | 결정 |
|----|------|
| Q1 | **EC2 + Docker Compose** (7서비스). 4차 시연 주 호스트는 Vercel 아님. |
| Q2 | `/prompts/{id}/` **인라인만** — `/prompts/{id}/agent/` 템플릿 라우트 없음. |
| Q3 | 보관함 탭 **「내 변환」** = 소유 프롬프트당 최신 `AgentTransformation` 1건; **`GET /api/accounts/me/transformations/`** |
| Q4 | **`AnalysisResult` MVP 제외** (analyze 태스크/API 없음). |
| Q5 | **`PromptEmbedding.vector` JSON** + numpy 코사인 유사도. |
| Q6 | **`Task.result_id` + `task_type`** (GenericForeignKey 없음). |
| Q7 | **`POST .../transform/`** 호출 및 변환 버튼은 **작성자만**. |
| Q8 | **`mcp_package` DB choices만**; UI 비활성 / 준비 중. |
| Q9 | **수동 「에이전트로 변환」 버튼만** (생성 시 자동 enqueue 없음). |
| Q10 | **기본 `LLM_PROVIDER=mock`**; HF 시연 시에만 `huggingface` 전환. |
| Q11 | **WebSocket** 태스크 알림 + `prompt-detail.js` **폴링 fallback**. |
| Q12 | phase 문서는 **3·4차만** 다룸. |
| Q13 | **Context Policy + Harness Policy** 풀세트 — 변환 단계마다 자동 생성·DB 저장·상세 UI 표시. 정책 **실제 실행**(요약·벡터 query·재시도)은 출시 후 로드맵. |

## Q13. Context Policy + Harness Policy 메타데이터 (Option 3)

**결정**: 풀세트 채택 — 각 변환 단계에 Context Policy와 Harness Policy를 자동 생성·저장·표시.

**적용 범위 (MVP)**:
- 정책 생성 (LLM 자동 또는 mock 고정)
- 정책 DB 저장 (`AgentTransformation.decomposed_steps[].context_policy/harness_policy`)
- 정책 UI 표시 (상세 페이지 인라인 카드)
- 정책 실제 실행 (요약, 벡터 query, 재시도 정밀 적용) — 5차/출시 후 로드맵

**근거**: 3차 발표 피드백("하네스를 공유하는 쪽으로 발전") 정면 답변.
