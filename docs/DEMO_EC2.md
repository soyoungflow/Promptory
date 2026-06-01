# Phase 4 Demo on EC2 (Docker Compose)

Aligned with [DECISIONS.md](./phases/DECISIONS.md), [WBS_SCHEDULE_0602_0608.md](./phases/WBS_SCHEDULE_0602_0608.md), and the 4th evaluation checklist.

## Stack (7 services)

| Service | URL (on EC2) |
|---------|----------------|
| Django (daphne) | `http://<EC2_HOST>:8000/` |
| FastAPI | `http://<EC2_HOST>:8001/docs` |
| Prometheus | `http://<EC2_HOST>:9090/` |
| Grafana | `http://<EC2_HOST>:3000/` (admin / admin) |

## Deploy (existing CD or manual)

```bash
cd /path/to/Promptory
git pull origin main
cp .env.example .env   # once — set SECRET_KEY, LLM_PROVIDER=mock
docker compose up -d --build
docker compose exec web python manage.py migrate --noinput
```

## HF demo (evaluation only)

```bash
# In .env on EC2
LLM_PROVIDER=huggingface
```

Rebuild `ai_server` with HF dependencies (`ai_server/requirements-hf.txt` if added) and allow 10–15 min first model download. For rehearsal use **mock** (default).

## 21-step demo script (short)

1. Open home → explore prompts (3차 유지)
2. Login as author
3. Open own prompt detail → **에이전트로 변환하기**
4. Show PENDING → SUCCESS (polling or WebSocket)
5. Inline 4-step agent result + confidence
6. Library → **내 변환** tab (latest per prompt)
7. `GET /api/tasks/{id}/status/` in browser devtools or Postman
8. FastAPI `/docs` → `/transform` mock call
9. Prometheus targets UP, Grafana dashboard
10. Admin → Task / AgentTransformation rows

## Security groups

Open: **8000**, **8001**, **9090**, **3000** (or tunnel for demo).
