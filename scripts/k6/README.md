# k6 부하 테스트 (가산점 +2)

## 설치

```bash
# macOS
brew install k6

# Ubuntu / WSL
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt update && sudo apt install k6
```

## 실행

```bash
# 로컬 Compose (nginx :80)
docker compose up -d
k6 run -e BASE_URL=http://127.0.0.1 scripts/k6/smoke.js

# EC2
k6 run -e BASE_URL=http://13.211.8.186 scripts/k6/smoke.js
```

## 발표에서 말할 것

1. **시나리오**: 동시 사용자 10명, 2분간 홈·목록 API·AI health 반복
2. **평균 vs p95**: 평균은 낮아도 꼬리 지연(p95)이 크면 Celery/DB 병목 신호
3. **에러율**: 5% 미만 threshold — nginx 502·타임아웃이 늘면 web/celery 상태 점검

상세 가산점 전략: [docs/BONUS_POINTS_PLAN.md](../../docs/BONUS_POINTS_PLAN.md)
