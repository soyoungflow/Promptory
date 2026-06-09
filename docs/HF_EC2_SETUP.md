# Hugging Face 연결 (EC2)

[DECISIONS Q10](./phases/DECISIONS.md): 일상·리허설은 `mock`, HF 시연 시 `huggingface`.

## 모델 구성

| 역할 | 환경변수 | 권장 값 |
|------|----------|---------|
| 프롬프트 → 4단계 분해 | `HF_MODEL_NAME` | 아래 표 참고 |
| 유사 프롬프트 임베딩 | `HF_EMBEDDING_MODEL` | `jhgan/ko-sroberta-multitask` |
| 메모리 절약 | `HF_TORCH_DTYPE` | `float16` |

### Transform LLM 선택

| 모델 | 용도 |
|------|------|
| **`Qwen/Qwen2.5-1.5B-Instruct`** | **로컬/WSL 또는 EC2 4GB+** — HF 연결 검증 |
| `LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct` | 프로젝트 명세·발표 스토리 — **RAM 8GB+** |
| t3.micro **2GB** | 실측 OOM(exit 137) — **발표는 mock**, HF는 로컬 또는 인스턴스 업그레이드 |
| `mock` (기본) | 발표 본선 E2E — 빠르고 안정 |

> `EXAONE-3.5-0.8B` 는 Hugging Face에 없습니다.

### 인스턴스 타입 vs 모델

| EC2 타입 | RAM | HF Transform 권장 |
|----------|-----|-------------------|
| t3.micro / t3.small | 2GB | **mock만** (실측 OOM) |
| **t3.medium** | **4GB** | **Qwen2.5-1.5B** + ko-sroberta |
| t3.large | 8GB | EXAONE-3.5-2.4B 시도 가능 |

---

## EC2 t3.medium 업그레이드 (2GB → 4GB)

현재 t3.micro/small(2GB)에서 HF 로드 시 `exit 137`(OOM)이 납니다. **t3.medium(4GB)** 으로 올리면 Qwen 1.5B HF 시연이 현실적입니다.

### 1) AWS 콘솔에서 타입 변경

1. [EC2 콘솔](https://console.aws.amazon.com/ec2/) → **Instances**
2. 인스턴스 선택 → **Instance state** → **Stop instance** (완전히 `stopped` 될 때까지 대기)
3. **Actions** → **Instance settings** → **Change instance type**
4. **t3.medium** 선택 → **Change**
5. **Instance state** → **Start instance**

> 인스턴스를 **중지(stop)** 해야 타입 변경이 됩니다. 재부팅(reboot)만으로는 안 됩니다.

### 2) 공인 IP·접속 확인

| 항목 | 확인 |
|------|------|
| **Elastic IP 없음** | 시작 후 **퍼블릭 IP가 바뀔 수 있음** → 새 IP로 접속 |
| GitHub Secrets | `EC2_HOST`가 IP면 **Secrets 갱신** 후 CD 재실행 |
| `.env` | `ALLOWED_HOSTS`, `PUBLIC_BASE_URL`에 **새 IP** 반영 |
| 보안 그룹 | **TCP 80, 22** 유지 (인스턴스에 붙어 있으면 그대로) |
| SSH | `ssh -i ~/.ssh/promptory-key.pem ubuntu@<새_IP>` |

Elastic IP를 쓰면 IP 변경 없이 유지됩니다 (선택, 유료 가능).

### 3) EC2 접속 후 스펙·스택 확인

```bash
free -h          # Mem total ≈ 3.7~4 Gi
nproc            # 2 vCPU
cd ~/Promptory
docker compose ps
curl -s http://127.0.0.1/ai/health
```

스왑(2GB)은 이미 있으면 유지해도 됩니다. 4GB만으로도 Qwen 1.5B는 스왑 없이 동작하는 경우가 많습니다.

### 4) HF 모드 전환 (t3.medium 권장 설정)

```bash
cd ~/Promptory
nano .env
```

```bash
LLM_PROVIDER=huggingface
HF_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
HF_EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
HF_TORCH_DTYPE=float16
# ALLOWED_HOSTS, PUBLIC_BASE_URL — IP 바뀌었으면 수정
```

```bash
docker compose build ai_server    # 최초 HF 빌드 또는 코드 pull 후
docker compose up -d --build
docker compose logs -f ai_server  # 첫 실행: 모델 다운로드 5~15분
```

### 5) HF 동작 확인

```bash
curl -s http://127.0.0.1/ai/health
# provider: huggingface, model_loaded: true (첫 /transform 후)

curl -s -X POST http://127.0.0.1/ai/transform \
  -H 'Content-Type: application/json' \
  -d '{"prompt_text":"블로그 SEO 글 작성 프롬프트 예시입니다.","max_steps":4}'
```

브라우저: `http://<EC2_IP>/` → 로그인 → **에이전트로 변환** → 결과·Admin `model_used` 확인.

### 6) 발표 전략 (권장)

| 구분 | 설정 |
|------|------|
| **본 시연 E2E** | `LLM_PROVIDER=mock` (빠르고 안정) |
| **HF 증빙** | t3.medium에서 Qwen 1회 + `/ai/docs` 스크린샷 |
| **EXAONE 스토리** | 슬라이드·명세는 2.4B; 실연은 t3.large 또는 mock |

발표 직전 mock 복귀:

```bash
sed -i 's/^LLM_PROVIDER=.*/LLM_PROVIDER=mock/' .env
docker compose up -d --force-recreate ai_server celery_worker
```

### 7) 비용·주의 (대략)

- t3.medium: micro 대비 **약 2배** 과금 (리전·시간당 요금 확인)
- 평가 기간만 켜 두고, 끝나면 **Stop** 또는 다시 micro로 내리기 가능 (타입 변경은 stopped 상태에서)
- 디스크(EBS) 데이터는 타입 변경해도 **유지** (`~/Promptory`, Docker volume, HF cache)

---

## EC2 `.env` (HF — B안 검증)

```bash
LLM_PROVIDER=huggingface
HF_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
HF_EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
HF_TORCH_DTYPE=float16
FASTAPI_URL=http://ai_server:8000
```

EXAONE 시연(8GB+ 인스턴스):

```bash
HF_MODEL_NAME=LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct
```

발표 후 mock 복귀:

```bash
LLM_PROVIDER=mock
docker compose up -d --force-recreate ai_server celery_worker
```

## 스왑 (2GB RAM)

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
grep -q swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 빌드·기동

```bash
cd ~/Promptory
git pull origin main
docker compose build ai_server
docker compose up -d ai_server celery_worker
docker compose logs -f ai_server
```

`ai_server` 이미지: `requirements-hf.txt` (torch CPU, transformers, sentence-transformers).

## 확인

```bash
curl -s http://127.0.0.1/ai/health
curl -s -X POST http://127.0.0.1/ai/transform \
  -H 'Content-Type: application/json' \
  -d '{"prompt_text":"블로그 SEO 글 작성 프롬프트 예시입니다.","max_steps":4}'
```

- Swagger: `http://<EC2>/ai/docs`
- 앱: 로그인 → 본인 프롬프트 → **에이전트로 변환** → `model_used` 확인

## 발표 멘트 예

「리허설과 본 시연은 mock으로 E2E를 보여드리고, HF 경로는 Qwen/EXAONE으로 같은 `/transform` API에 연결되어 있습니다. 프로덕션에서는 EXAONE 2.4B와 한국어 임베딩을 씁니다.」

## 트러블슈팅

| 증상 | 조치 |
|------|------|
| OOM | 스왑, `float16`, Qwen 1.5B, 또는 t3.medium+ |
| `RopeParameters` ImportError | EXAONE → Qwen으로 전환 또는 transformers git main |
| invalid model identifier | `HF_MODEL_NAME` 오타 (0.8B 없음) |
| JSON parse 500 | 프롬프트 재시도; 발표는 mock |
