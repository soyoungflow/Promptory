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
