# Promptory — 트러블슈팅 (Phase 4)

WBS Day 7 시나리오 기준. 로컬 Docker Compose / EC2 공통.

---

## 1. `docker compose up` 후 web·nginx unhealthy

**증상:** `promptory-web-1` 또는 `promptory-nginx-1`이 `unhealthy`.

**확인:**
```bash
docker compose logs web --tail 50
docker compose logs nginx --tail 30
```

**흔한 원인:**
- DB 마이그레이션 실패 → `web` entrypoint에서 `migrate` 오류
- `ALLOWED_HOSTS`에 EC2 IP·`web` 미포함 → Django 400
- 호스트 80 포트 점유 (호스트 nginx 등)

**조치:**
```bash
docker compose run --rm web python manage.py migrate
# ALLOWED_HOSTS=localhost,127.0.0.1,web,<EC2_IP> (.env)
sudo systemctl stop nginx   # EC2 호스트 nginx 충돌 시
docker compose up -d --force-recreate web nginx
```

---

## 2. 변환 버튼 클릭 후 무한 대기 / 504

**증상:** 「에이전트로 변환하기」 후 스피너만 돌거나 nginx `504 Gateway Time-out`.

**확인:**
```bash
docker compose ps celery_worker
docker compose logs celery_worker --tail 40
curl -s http://localhost/ai/health
```

**흔한 원인:**
- `celery_worker` 미기동
- Redis broker 연결 실패
- `ai_server` OOM (HF 모델) 또는 `/health`가 모델 로드 중 블로킹 (구버전)

**조치:**
```bash
docker compose up -d redis celery_worker ai_server
# 발표/리허설: .env 에 LLM_PROVIDER=mock
docker compose up -d --force-recreate ai_server celery_worker
```

---

## 3. Celery Task가 PENDING에서 멈춤

**증상:** Admin Task 상태가 `PENDING`만 유지.

**확인:**
```bash
docker compose exec redis redis-cli ping   # PONG
docker compose logs celery_worker | grep ready
```

**조치:** worker 재시작, `CELERY_BROKER_URL`이 `redis://redis:6379/0`인지 `.env` 확인.

---

## 4. `ai_server` exit 137 (OOM)

**증상:** `docker compose ps`에서 `ai_server` Exited (137).

**원인:** RAM 부족 (EC2 t3.micro 2GB, WSL 8GB 미만 + 다른 컨테이너 동시 실행).

**조치:**
```bash
# .env
LLM_PROVIDER=mock
# 또는 더 작은 모델
HF_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
```
EC2 발표는 **mock 고정** 권장. HF 시연은 t3.medium(4GB)+ 또는 로컬 12GB+ WSL.

---

## 5. HF 변환 `LLM parse error`

**증상:** Task `FAIL`, `error_message`에 JSON 파싱 오류.

**원인:** 소형 LLM이 JSON 형식을 어김.

**조치:** 리허설·발표는 `mock`. HF 증빙은 `/ai/docs` + 1회 성공 스크린샷으로 대체.

---

## 6. WebSocket 연결 실패 (폴링 fallback)

**증상:** DevTools WS `failed`; UI는 폴링으로 완료됨.

**확인:** nginx `/ws/` 프록시, JWT `?token=` 전달.

```bash
curl -s http://localhost/   # nginx 경유
# 브라우저: ws://<host>/ws/tasks/?token=<access>
```

폴링 fallback(`GET /api/tasks/{id}/status/`)이 동작하면 시연 가능.

---

## 7. Grafana / Prometheus 빈 화면

**증상:** `/grafana/` 접속은 되나 AI 패널(`agent_transformation_total` 등) No data.

**확인:**
```bash
curl -fsS http://127.0.0.1/prometheus/prometheus/api/v1/targets | grep -E 'celery|django|fastapi'
docker compose exec celery_worker python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:9100/metrics').read()[:400])"
curl -fsS 'http://127.0.0.1/prometheus/prometheus/api/v1/query?query=sum(agent_transformation_total)'
```
커스텀 AI 메트릭은 **Celery worker `:9100/metrics`** 에서 수집됩니다. transform 1회 실행 후 Grafana를 새로고침하세요.

**조치:**
- `PUBLIC_BASE_URL`이 실제 접속 URL과 일치하는지 확인
- 변환 1회 실행 후 Celery worker 메트릭 생성 (`agent_transformation_total`)
- Grafana 대시보드: **Promptory Phase 4** (프로비저닝됨)

---

## 8. EC2 외부 접속 불가 (ERR_CONNECTION_TIMED_OUT)

**확인:** AWS 보안 그룹 **인바운드 TCP 80** (SSH 22). nginx 이전에는 8000도 필요했으나 현재는 **80만** 개방.

```bash
curl -s http://<EC2_IP>/
curl -s http://<EC2_IP>/ai/health
```

---

## 9. CD 배포 실패 — `no space left on device`

**증상:** GitHub Actions CD 단계 `[5/7] Rebuild`에서 Docker build 중 exit 1.

```
failed to extract layer ... no space left on device
```

**원인:** EC2 기본 EBS(8GB)에 HF(torch) 이미지·빌드 캐시·이전 레이어 누적.

**즉시 조치 (EC2 SSH):**
```bash
cd /path/to/Promptory
docker compose down
docker builder prune -af
docker system prune -af
df -h /
docker compose up -d --build
```

**여전히 부족하면:** EBS 볼륨 **20GB+** 로 확장 (AWS 콘솔 → Volume → Modify → grow partition).

**예방:** CD 워크플로가 배포 전 `docker builder prune` / `docker system prune` 을 실행함 (`.github/workflows/cd.yml`).

---

## 9. CD smoke check `502` (Grafana DNS 실패)

**증상:** `/`, `/ai/health` 는 200인데 `/grafana/api/health` 만 502. nginx 로그에 `grafana could not be resolved (2: Server failure)`.

**원인:** **Grafana 컨테이너가 떠 있지 않음** — `docker compose ps` 에 `promptory-grafana-1` 이 없으면 nginx 가 upstream 호스트 `grafana` 를 DNS 로 찾지 못함.

**즉시 조치 (EC2 SSH):**
```bash
cd ~/Promptory
docker compose ps -a
docker compose up -d grafana prometheus
docker compose logs grafana --tail 80
curl -fsS http://127.0.0.1/grafana/api/health
```

**종료(exited)·CrashLoop 상태면:** `docker compose logs grafana` 확인.

- **Grafana 13 + provisioning uid 불일치** (로그: `Datasource provisioning error: data source not found`): 기존 `grafana_data` 볼륨의 datasource UID 와 `grafana/provisioning/datasources/prometheus.yml` 의 `uid: Prometheus` 가 맞지 않으면 Grafana 13 이 기동 실패함.
```bash
docker compose stop grafana
docker volume rm promptory_grafana_data
docker compose up -d grafana prometheus
curl -fsS http://127.0.0.1/grafana/api/health
```
- 프로젝트는 `grafana/grafana:11.4.0` 으로 고정해 이 회귀를 피함.

**예방:** `docker-compose.yml` — grafana `11.4.0` 고정, `restart: unless-stopped`, healthcheck. CD는 grafana/prometheus 기동·healthy 대기 후 smoke check 실행.

---

## 10. CD smoke check `502 Gateway Time-out` (nginx/web 미준비)

**증상:** smoke check 초반 `curl http://127.0.0.1/` 자체가 502. `nginx` 가 `(health: starting)`.

**원인:** `compose up` 직후 nginx·web 이 아직 기동 중.

**조치:** CD `[7/9]` 에서 db/redis/ai_server/web/nginx/grafana 가 `healthy` 될 때까지 대기 후 smoke 실행.

---

## 빠른 복구 체크리스트

```bash
cd Promptory
docker compose down
docker compose up -d --build
docker compose ps
curl -fsS http://localhost/
curl -fsS http://localhost/ai/health
docker compose run --rm web python manage.py seed_mockup   # 최초/데모 데이터
```

발표 직전: `LLM_PROVIDER=mock`, `seed_mockup` 완료, 슈퍼유저 로그인 확인.
