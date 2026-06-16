# 가산점 증빙 제출 폴더

발표 전 아래 구조를 채운 뒤 제출·시연에 사용합니다.

```
submission/
├─ evidence/           # PNG 캡처 (01~08, 예비 09~12)
├─ docs/
│  ├─ k6_result.md     # k6 실행 후 수치 채우기
│  └─ troubleshooting.md  # cp ../docs/troubleshooting.md docs/
└─ BONUS_SUMMARY.md    # 항목·점수·증빙 매핑표
```

## 제출 전

1. `cp docs/troubleshooting.md submission/docs/troubleshooting.md`
2. k6 실행 후 `submission/docs/k6_result.md` 수치 채우기
3. `evidence/`에 캡처 PNG 저장 (파일명은 `BONUS_SUMMARY.md` 참고)
4. EC2 배포 후 `collectstatic` 반영 (`blueprint-design.js` WS 연동 포함)

## WebSocket 시연 (③)

설계서 변환 시작 → DevTools Network → WS → `ws/tasks/?token=...`  
화면 하단 힌트: `WebSocket 연결됨` → `WebSocket push · Task SUCCESS`
