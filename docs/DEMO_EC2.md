# Phase 4 EC2 시연 (Docker Compose)

[DECISIONS.md](./phases/DECISIONS.md), [WBS_SCHEDULE_0602_0608.md](./phases/WBS_SCHEDULE_0602_0608.md), 4차 평가 자가정검 체크리스트와 정렬되어 있습니다.

## 스택 (7개 서비스)

| Service | URL (EC2 기준) |
|---------|----------------|
| Django (daphne) | `http://<EC2_HOST>:8000/` |
| FastAPI | `http://<EC2_HOST>:8001/docs` |
| Prometheus | `http://<EC2_HOST>:9090/` |
| Grafana | `http://<EC2_HOST>:3000/` (admin / admin) |

## 배포 (기존 CD 또는 수동)

```bash
cd /path/to/Promptory
git pull origin main
cp .env.example .env   # 최초 1회 — SECRET_KEY, LLM_PROVIDER=mock 설정
docker compose up -d --build
docker compose exec web python manage.py migrate --noinput
```

## HF 시연 (평가용만)

```bash
# EC2 .env
LLM_PROVIDER=huggingface
```

HF 의존성이 포함된 `ai_server` 이미지로 재빌드(`ai_server/requirements-hf.txt` 추가 시) 후, 첫 모델 다운로드에 10~15분 소요될 수 있습니다. 리허설은 **mock**(기본값) 사용을 권장합니다.

## 21단계 시연 스크립트 (요약)

1. 홈 → 프롬프트 탐색 (3차 유지)
2. 작성자 계정으로 로그인
3. 본인 프롬프트 상세 → **에이전트로 변환하기**
4. PENDING → SUCCESS 표시 (폴링 또는 WebSocket)
5. 인라인 4단계 에이전트 결과 + confidence
6. 보관함 → **내 변환** 탭 (프롬프트당 최신 1건)
7. 브라우저 개발자 도구 또는 Postman에서 `GET /api/tasks/{id}/status/`
8. FastAPI `/docs` → `/transform` mock 호출
9. Prometheus targets UP, Grafana 대시보드
10. Admin → Task / AgentTransformation 행 확인

## 보안 그룹

개방 포트: **8000**, **8001**, **9090**, **3000** (또는 시연 시 SSH 터널 사용).
