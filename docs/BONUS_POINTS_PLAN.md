# 선택 기능 가산점 전략 (최대 +20점)

평가 기준: [4차 발표가이드 및 평가기준.md](./4차%20발표가이드%20및%20평가기준.md) §D  
**규칙:** 코드만 있으면 인정 안 됨 → **발표에서 시연 + 1~2문장 설명** 필수.

---

## k6 부하 테스트란? (+2점)

### 한 줄 정의

**가상 사용자가 API·웹에 동시에 요청을 쏘아, 서버가 버티는지·얼마나 느려지는지 숫자로 재는 도구**입니다.

### 비유

매장에 손님이 1명일 때와 50명이 동시에 들어올 때 계산대 대기 시간이 어떻게 달라지는지 **시뮬레이션**하는 것과 같습니다.

### k6가 보여주는 지표

| 지표 | 의미 | 발표 멘트 예시 |
|------|------|----------------|
| **RPS** | 초당 처리 요청 수 | "동시 10명에서 초당 N건 처리" |
| **평균 응답** | 대부분 요청의 체감 속도 | "목록 API 평균 120ms" |
| **p95** | 상위 5% 느린 요청 | "꼬리 지연이 800ms — Celery·DB 확인 필요" |
| **에러율** | 5xx·타임아웃 비율 | "2% 미만이면 시연 환경에서 안정" |

### Promptory 실행

```bash
k6 run -e BASE_URL=http://13.211.8.186 scripts/k6/smoke.js
```

스크립트: `scripts/k6/smoke.js` — 홈, `/api/prompts/`, `/ai/health` 부하.

### 발표 슬라이드 1장 구성 (권장)

1. k6 실행 명령 캡처
2. 터미널 요약 (평균, p95, 에러율)
3. Grafana HTTP 패널과 나란히 — "부하 전후 RPS·지연 비교"
4. 병목 한 줄: "mock AI라 CPU 병목은 nginx+Django, 실 HF면 ai_server가 병목"

---

## Kubernetes / HPA란?

### Kubernetes (K8s) (+4점, ConfigMap/Secret +2점)

**도커 컨테이너 여러 개를 클러스터에서 자동으로 띄우고, 죽으면 다시 살리고, 네트워크·설정을 통합 관리하는 운영 플랫폼**입니다.

| Docker Compose (현재) | Kubernetes |
|----------------------|------------|
| 한 EC2에서 `docker compose up` | 여러 노드에 Pod 분산 |
| 수동 `scale` | 선언적 YAML + 컨트롤러 |
| `.env` 파일 | **ConfigMap**(설정) + **Secret**(비밀) |

**ConfigMap / Secret (+2점):** DB URL, `SECRET_KEY`, `FASTAPI_URL`을 이미지 밖 YAML로 분리해 환경별로 바꾸는 패턴.

### HPA — Horizontal Pod Autoscaler (+2점)

**CPU·메모리(또는 커스텀 메트릭)가 임계치를 넘으면 Pod 개수를 자동으로 늘리고, 한가하면 줄이는 오토스케일러**입니다.

```
부하 증가 → CPU 70% 초과 → web Pod 2개 → 5개
부하 감소 → CPU 여유 → Pod 다시 2개
```

비유: 계산대 줄이 길어지면 **직원(web Pod)을 자동으로 더 배치**하는 것.

### Promptory에 K8s를 안 쓰는 이유 (발표에서 솔직히)

- 4차 시연 호스트는 **EC2 + Compose** (DECISIONS Q1).
- K8s 클러스터 구축·학습 비용이 크고, 발표 15분 안에 **실제 스케일링 시연**이 어렵다.

### K8s 가산점을 받고 싶다면 (현실적 옵션)

| 옵션 | 난이도 | 발표 가능성 |
|------|--------|-------------|
| **A. 슬라이드 + 아키텍처만** | 낮음 | 가산점 **불인정** (시연 없음) |
| **B. kind/minikube 로컬 1회** | 중 | `kubectl get pods` + `kubectl apply` 시연 가능 |
| **C. EKS/GKE 프로덕션** | 높음 | 비용·시간 대비 4차에 비추천 |

**권장:** 이번 주는 **k6 (+2)** 로 빠르게 확보. K8s는 "로드맵" 슬라이드 1장으로만 언급.

참고 매니페스트(학습·리허설용): `k8s/README.md` (선택).

---

## 이미 확보 가능한 가산점 (코드 ✅ → 발표 시연만 남음)

| 항목 | 점수 | 시연 방법 (30초~1분) |
|------|------|----------------------|
| WebSocket 실시간 알림 | +3 | DevTools → WS `ws/tasks/` 연결, 설계서 변환 중 메시지 |
| polling 외 실시간 구조 | +2 | "폴링 fallback 있지만 WS 우선" 설명 |
| structlog task_id 추적 | +2 | Celery 로그에 `task_id=` 한 줄 보여주기 |
| local / docker / production 설정 | +2 | `config/settings/` 폴더 구조 |
| Nginx 리버스 프록시 | +2 | `:80` 하나로 Django·FastAPI·Grafana |
| GitHub Actions CI | +2 | Actions 탭 녹색 체크 |
| GitHub Actions CD | +3 | push → EC2 자동 배포 로그 |
| Prometheus | +2 | `/prometheus/` targets UP |
| Grafana | +2 | Phase 4 대시보드 패널 |
| 커스텀 메트릭 | +3 | `agent_transformation_total` 쿼리 1회 |
| 트러블슈팅 문서 | +2 | `docs/troubleshooting.md` prometheus·static 이슈 |
| AI 고도화 (유사도) | +3 | 상세 페이지 유사 레시피 또는 `/similar/` API |
| **k6 부하 테스트** | +2 | `scripts/k6/smoke.js` 실행 결과 |

**합계 예시 (상한 20점):** CD(+3) + 커스텀메트릭(+3) + WS(+3) + Prometheus(+2) + Grafana(+2) + Nginx(+2) + k6(+2) + 트러블슈팅(+2) = **19점**

---

## 발표 15분 안 가산점 노출 순서 (추천)

1. **아키텍처 슬라이드** — Nginx 단일 포트 (+2)
2. **라이브 시연** — 설계서 만들기 + WS (+3, +2)
3. **Grafana** — 커스텀 메트릭 (+3, +2, +2)
4. **GitHub Actions** — CI/CD 탭 10초 (+2, +3)
5. **k6 결과 슬라이드** 20초 (+2)
6. (선택) troubleshooting 한 줄 (+2) — 시간 없으면 슬라이드 각주

K8s/HPA는 **"Phase 5 로드맵"** 1슬라이드로만 — 점수 욕심내지 말고 필수 E2E 완료가 우선.
