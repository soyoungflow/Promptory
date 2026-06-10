# Kubernetes 참고 (선택 · 가산점 +4/+2/+2)

> **4차 발표 주 배포는 EC2 Docker Compose입니다.**  
> 이 폴더는 K8s/HPA 가산점을 **학습·리허설**할 때만 사용하세요.

## 개념 요약

- **Deployment**: `web`, `ai_server` Pod를 N개 유지
- **Service**: 클러스터 내부 DNS (`web:8000`)
- **ConfigMap**: `ALLOWED_HOSTS`, `LLM_PROVIDER=mock` 등 비밀 아닌 설정
- **Secret**: `SECRET_KEY`, `DB_PASSWORD` (base64)
- **HPA**: `web` Deployment의 CPU 70% 초과 시 replicas 2→5

## 로컬 리허설 (kind 예시)

```bash
kind create cluster --name promptory
kubectl apply -f k8s/namespace.yaml
# Secret은 로컬 값으로 직접 생성 후
kubectl apply -f k8s/web-deployment.yaml
kubectl apply -f k8s/web-hpa.yaml
kubectl get pods -n promptory
kubectl get hpa -n promptory
```

발표에서 인정받으려면 **kubectl get pods / hpa** 화면을 실제로 보여주고, Compose 대비 차이를 1분 설명하세요.

상세 전략: [docs/BONUS_POINTS_PLAN.md](../docs/BONUS_POINTS_PLAN.md)
