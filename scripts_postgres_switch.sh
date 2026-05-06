#!/bin/bash
# =============================================
# PostgreSQL 전환 스크립트
# 실행 전 조건: CRUD 기능 완성 + 모델 구조 안정
# =============================================

echo "=== Promptory PostgreSQL 전환 ==="

# 1. PostgreSQL DB 생성
echo "[1/5] PostgreSQL DB 생성"
psql -U postgres -c "CREATE DATABASE promptory_db;" 2>/dev/null || echo "  → DB가 이미 존재하거나 psql 미설치"

# 2. production 설정 모듈 사용
echo "[2/5] production 설정 모듈 사용"
export DJANGO_SETTINGS_MODULE=config.settings.production

# 3. migration 파일 정리 확인
echo "[3/5] migration 파일 확인"
python manage.py showmigrations --settings=config.settings.production

# 4. migrate 실행
echo "[4/5] migrate 실행"
python manage.py migrate --settings=config.settings.production

# 5. E2E 체크
echo "[5/5] system check"
python manage.py check --settings=config.settings.production

echo ""
echo "✅ PostgreSQL 전환 완료"
echo "   슈퍼유저 생성: python manage.py createsuperuser"
