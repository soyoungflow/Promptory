# Phase 4 — Resolved Decisions (2026-05-27)

Locked for implementation. Evaluation refs: `docs/4차 발표가이드 및 평가기준.md`, `docs/자가정검 체크리스트(개인프로젝트).md`.

| ID | Decision |
|----|----------|
| Q1 | **EC2 + Docker Compose** (7 services). Not Vercel for 4th demo. |
| Q2 | **Inline only** on `/prompts/{id}/` — no `/prompts/{id}/agent/` template route. |
| Q3 | Library tab **“My transformations”** = latest `AgentTransformation` per owned prompt; **`GET /api/accounts/me/transformations/`** |
| Q4 | **`AnalysisResult` out of MVP** (no analyze task/API). |
| Q5 | **`PromptEmbedding.vector` as JSON** + numpy cosine similarity. |
| Q6 | **`Task.result_id` + `task_type`** (no GenericForeignKey). |
| Q7 | **Author only** may call `POST .../transform/` (and sees transform button). |
| Q8 | **`mcp_package` in DB choices**; UI disabled / coming soon. |
| Q9 | **Manual “Convert to agent” button** only (no auto-enqueue on create). |
| Q10 | **Default `LLM_PROVIDER=mock`**; switch to `huggingface` for HF demo only. |
| Q11 | **WebSocket** task updates + **polling fallback** in `prompt-detail.js`. |
| Q12 | Phase docs cover **3 and 4 only**. |
