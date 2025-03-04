#!/bin/bash

# 로컬 스토리지 권한 설정
echo "🚀 Setting permissions for mounted volumes..."

# 권한을 777로 변경할 디렉토리 목록
DIRS=(
    "/home/yewon/job-interview-data/airflow/dags"
    "/home/yewon/job-interview-data/airflow/logs"
    "/home/yewon/job-interview-data/airflow/plugins"
    "/home/yewon/job-interview-data/crawling/results"
    "/home/yewon/job-interview-data/crawling/employment_detail"
    "/home/yewon/job-interview-data/setting_object_storage"
    "/home/yewon/job-interview-data/crawling/logs"
)

# 각 디렉토리에 대해 권한 변경
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "🔧 Changing permissions for $dir"
        sudo chmod -R 777 "$dir"
        sudo chown -R "$(whoami)":"$(whoami)" "$dir"
    else
        echo "⚠️ Warning: Directory $dir does not exist. Skipping..."
    fi
done

echo "✅ All necessary directories have been updated."


echo "🚀 Starting Airflow with Docker Compose..."


# 1️⃣ 실행할 Docker Compose 파일 확인
COMPOSE_FILE="docker-compose.yaml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: $COMPOSE_FILE not found! Please check the path."
    exit 1
fi

# env 파일 확인
if [ ! -f "../.env" ]; then
    echo "❌ Error: .env file not found! Please check the path."
    exit 1
fi

if [ -f "../.env" ]; then
    set -a        # 모든 변수를 자동으로 export 하도록 설정
    . ../.env     # .env 파일의 내용을 로드
    set +a        # 다시 자동 export 해제
fi


# 2️⃣ Docker Compose 실행
echo "🐳 Running Docker Compose..."
docker compose --env-file ../.env up --build --remove-orphans -d

# 3️⃣ PostgreSQL이 완전히 실행될 때까지 대기
echo "⏳ Waiting for PostgreSQL to become available..."
timeout=60
elapsed=0

# PostgreSQL 컨테이너가 실행 중인지 확인
if ! docker ps --filter "name=postgres_airflow" --format "{{.Names}}" | grep -q "postgres_airflow"; then
    echo "❌ Error: PostgreSQL container 'postgres_airflow' is not running!"
    exit 1
fi

until docker exec postgres_airflow pg_isready -U airflow -d airflow; do
    echo "⏳ PostgreSQL is not ready yet, waiting..."
    sleep 3
done
echo "✅ PostgreSQL is ready!"



# 4️⃣ 컨테이너가 완전히 실행될 때까지 대기
echo "⏳ Waiting for Airflow containers to start..."
sleep 10  # 컨테이너가 완전히 실행될 시간을 줌

# 5️⃣ Airflow 컨테이너 ID 확인
AIRFLOW_WEBSERVER_CONTAINER=$(docker ps -qf "name=airflow_webserver")
AIRFLOW_SCHEDULER_CONTAINER=$(docker ps -qf "name=airflow_scheduler")

if [ -z "$AIRFLOW_WEBSERVER_CONTAINER" ] || [ -z "$AIRFLOW_SCHEDULER_CONTAINER" ]; then
    echo "❌ Error: Airflow containers are not running!"
    exit 1
fi

echo "airflow webserver container id : $AIRFLOW_WEBSERVER_CONTAINER"
echo "airflow scheduler container id : $AIRFLOW_SCHEDULER_CONTAINER"

# 6️⃣ Airflow Webserver & Scheduler Health Check
echo "⏳ Checking health of Airflow services..."
timeout=60
elapsed=0

while true; do
    WEB_HEALTH=$(docker inspect --format "{{json .State.Health.Status }}" airflow_webserver)
    SCHEDULER_HEALTH=$(docker inspect --format "{{json .State.Health.Status }}" airflow_scheduler)

    if [[ "$WEB_HEALTH" == "\"healthy\"" && "$SCHEDULER_HEALTH" == "\"healthy\"" ]]; then
        echo "✅ Airflow Webserver and Scheduler are healthy!"
        break
    fi

    echo "⏳ Waiting for Airflow Webserver ($WEB_HEALTH) and Scheduler ($SCHEDULER_HEALTH)..."
    sleep 5
    elapsed=$((elapsed + 5))

    if [ $elapsed -ge $timeout ]; then
        echo "❌ Error: Airflow services did not become ready in time."
        # 웹서버가 unhealthy이면 로그 출력
        if [ "$WEB_HEALTH" != "\"healthy\"" ]; then
            echo "📄 Airflow Webserver logs:"
            docker logs airflow_webserver
        fi
        # 웹서버가 unhealthy이면 로그 출력
        if [ "$SCHEDULER_HEALTH" != "\"healthy\"" ]; then
            echo "📄 Airflow Scheduler logs:"
            docker logs airflow_scheduler
        fi
        exit 1
    fi
done

# 7️⃣ Minio Health Check
echo "⏳ Checking health of Minio service..."
timeout=60
elapsed=0

while true; do
    MINIO_HEALTH=$(docker inspect --format "{{json .State.Health.Status }}" minio)
    if [[ "$MINIO_HEALTH" == "\"healthy\"" ]]; then
        echo "✅ Minio is healthy!"
        break
    fi

    echo "⏳ Waiting for Minio to become healthy ($MINIO_HEALTH)..."
    sleep 5
    elapsed=$((elapsed + 5))
    
    if [ $elapsed -ge $timeout ]; then
        echo "❌ Error: Minio did not become healthy in time."
        echo "📄 Minio logs:"
        docker logs minio
        exit 1
    fi
done

# 8️⃣ Admin 유저 생성 여부 확인 및 실행
echo "🔍 Checking if admin user exists..."
: "${AIRFLOW_ADMIN_USERNAME:?❌ Error: AIRFLOW_ADMIN_USERNAME is missing!}"
: "${AIRFLOW_ADMIN_PASSWORD:?❌ Error: AIRFLOW_ADMIN_PASSWORD is missing!}"
: "${AIRFLOW_ADMIN_EMAIL:?❌ Error: AIRFLOW_ADMIN_EMAIL is missing!}"


docker exec "$AIRFLOW_WEBSERVER_CONTAINER" bash -c "
airflow users list | grep -w '${AIRFLOW_ADMIN_USERNAME}' || 
(
    echo '👤 Creating Airflow admin user...'
    airflow users create \
        --username '${AIRFLOW_ADMIN_USERNAME}' \
        --password '${AIRFLOW_ADMIN_PASSWORD}' \
        --firstname 'Yewon' \
        --lastname 'Hwang' \
        --role 'Admin' \
        --email '${AIRFLOW_ADMIN_EMAIL}'
)"


echo "✅ Airflow is now running! Access it at: http://localhost:8080"

# 9️⃣ DAG 실행 대기 및 트리거
echo "🔍 Checking if 'daily_crawling_and_upload' DAG exists..."
if docker exec "$AIRFLOW_SCHEDULER_CONTAINER" airflow dags list | grep -w "daily_crawling_and_upload" > /dev/null; then
    echo "✅ 'daily_crawling_and_upload' DAG exists. Displaying DAG list:"
    docker exec "$AIRFLOW_SCHEDULER_CONTAINER" airflow dags list
else
    echo "🚀 'daily_crawling_and_upload' DAG not found. Triggering DAG..."
    docker exec "$AIRFLOW_SCHEDULER_CONTAINER" airflow dags trigger daily_crawling_and_upload
fi

