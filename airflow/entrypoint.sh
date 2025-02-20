#!/bin/bash
set -e  # 오류 발생 시 즉시 종료

# 환경 변수가 정상적으로 로드되었는지 로그 출력
echo "Airflow Admin Username: ${AIRFLOW_ADMIN_USERNAME}"
echo "Airflow Admin Email: ${AIRFLOW_ADMIN_EMAIL}"

echo "🔹 Airflow DB 연결 확인: ${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}"


# MySQL이 준비될 때까지 대기
echo "⏳ Waiting for MySQL database to be ready..."
until nc -z mysql 3306; do
  sleep 2
  echo "⌛ Waiting for MySQL..."
done


# Airflow DB 초기화
airflow db migrate

# 기존 사용자 삭제 (존재하면)
airflow users delete --username "${AIRFLOW_ADMIN_USERNAME}" || true

# 새로운 관리자 사용자 생성
airflow users create \
    --username "${AIRFLOW_ADMIN_USERNAME}" \
    --password "${AIRFLOW_ADMIN_PASSWORD}" \
    --firstname "${AIRFLOW_ADMIN_FIRSTNAME}" \
    --lastname "${AIRFLOW_ADMIN_LASTNAME}" \
    --role Admin \
    --email "${AIRFLOW_ADMIN_EMAIL}"

# Airflow 웹서버 실행
exec airflow webserver
