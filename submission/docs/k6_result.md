# k6 부하 테스트 결과

**실행일:** YYYY-MM-DD  
**대상:** `http://13.211.8.186` (또는 실제 EC2 URL)  
**스크립트:** `scripts/k6/smoke.js`

## 실행 명령

```bash
k6 run -e BASE_URL=http://13.211.8.186 scripts/k6/smoke.js
```

## 요약 수치

| 지표 | 값 | 비고 |
|------|-----|------|
| **가상 사용자 (VU)** | peak 10 | stages: 30s→5, 1m→10, 30s→0 |
| **RPS** | _채우기_ | `http_reqs` / duration |
| **평균 응답** | _채우기_ | `http_req_duration` avg |
| **p95 응답** | _채우기_ | `http_req_duration` p(95) |
| **에러율** | _채우기_ | `http_req_failed` rate |
| **체크 통과율** | _채우기_ | checks `succeeded` |

## 엔드포인트별 (스크립트 커스텀 메트릭)

| 엔드포인트 | 평균 (ms) | p95 (ms) |
|------------|----------:|---------:|
| `/` (home) | | |
| `/api/prompts/` | | |
| `/ai/health` | | |

## 해석 (1~2문장)

> _예: 평균 120ms, p95 800ms, 에러율 2% 미만. mock AI 환경이라 병목은 nginx+Django 구간이며, 실 HF 모드에서는 ai_server CPU가 병목이 될 것으로 예상._

## 증빙

- 터미널 요약 캡처: `../evidence/08_k6_summary.png`
- (선택) Grafana HTTP 패널 부하 전후: `../evidence/08_k6_grafana.png`

## 발표 멘트

> "k6로 동시 10 VU 부하를 걸었을 때 p95 _N_ms, 에러율 _N_%로 안정적이었습니다."
