# 가산점 증빙 제출 패키지 (상한 +20)

> **인정 규칙:** 구현 + 발표 시연 + 1~2문장 설명 — 3종 모두 필요. 코드만으로는 0점.

## 점수 설계

| # | 항목 | 점수 | 증빙 파일 | 발표 멘트 (1~2문장) |
|---|------|-----:|-----------|---------------------|
| 1 | GitHub Actions CD | +3 | `evidence/01_cd_actions.png` | main push 시 EC2 자동 배포, healthy 대기 후 smoke 통과 |
| 2 | 커스텀 메트릭 | +3 | `evidence/02_custom_metric_prom.png`, `02_custom_metric_grafana.png` | AI 변환 횟수·처리시간을 직접 정의한 커스텀 메트릭 |
| 3 | WebSocket 실시간 | +3 | `evidence/03_ws_devtools.png` | 폴링이 아니라 WebSocket으로 Task 상태를 실시간 push |
| 4 | AI 고도화(유사도) | +3 | `evidence/04_similar_api.png` | 임베딩 벡터 기반 유사 레시피 추천 |
| 5 | Prometheus | +2 | `evidence/05_prometheus_targets.png` | django·fastapi·celery scrape targets UP |
| 6 | Grafana | +2 | `evidence/06_grafana_dashboard.png` | Phase 4 대시보드에 운영 지표 시각화 |
| 7 | Nginx 단일 포트 | +2 | `evidence/07_nginx_single_port.png` | Nginx 리버스 프록시로 80포트 단일 진입점 |
| 8 | k6 부하 테스트 | +2 | `evidence/08_k6_summary.png`, `docs/k6_result.md` | 부하 전후 RPS·지연 비교 |
| 9 | 트러블슈팅 문서 | +2 | `docs/troubleshooting.md` | 운영 중 겪은 이슈와 해결을 문서화 |

**핵심 1~9 합 = 22 → 상한 +20.** 하나 실패해도 +20 유지.

## 예비 (백업)

| 항목 | 점수 | 증빙 |
|------|-----:|------|
| GitHub Actions CI | +2 | `evidence/09_ci_actions.png` |
| structlog task_id | +2 | `evidence/10_structlog_task_id.png` |
| 설정 분리 | +2 | `evidence/11_settings_split.png` |
| 폴링 fallback | +2 | `evidence/12_polling_fallback.png` |

## 캡처 체크리스트

- [ ] 01 CD Actions 성공 run (SSH → compose → smoke)
- [ ] 02 Prometheus `sum(agent_transformation_total)` + Grafana 패널
- [ ] 03 DevTools WS `ws/tasks/?token=...` 프레임
- [ ] 04 유사 레시피 UI 또는 `/api/prompts/{id}/similar/`
- [ ] 05 `/prometheus/targets` — django, fastapi, celery UP
- [ ] 06 Grafana Phase 4 대시보드
- [ ] 07 `/`, `/ai/docs`, `/grafana/` 동일 호스트 80포트
- [ ] 08 k6 실행 터미널 요약
- [ ] 09 `docs/troubleshooting.md` 제출

## 캡처 순서 (한 세션)

1. 변환 2~3회 (메트릭·그래프 채우기)
2. 변환 중 WS DevTools 캡처
3. Prometheus·Grafana·커스텀 메트릭
4. 유사도 / Nginx 경로
5. GitHub Actions CD (및 CI)
6. k6 실행 + `docs/k6_result.md` 작성
