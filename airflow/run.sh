#!/bin/bash

echo "🚀 Starting Airflow with Docker Compose..."

# 1️⃣ WSL2 환경인지 확인
if grep -qi "microsoft" /proc/version; then
    echo "🔍 Detected WSL2 environment."

    # WSL2의 현재 IP 가져오기
    WSL_IP=$(hostname -I | awk '{print $1}')
    echo "🖥️ WSL2 IP: $WSL_IP"

    # 2️⃣ 기존 포트포워딩 삭제 (오류 무시)
    echo "🛠️ Removing old port forwarding rules..."
    powershell.exe -Command "netsh interface portproxy delete v4tov4 listenport=8080" 2>/dev/null

    # 3️⃣ 새로운 포트포워딩 추가 (Admin 권한 필요)
    echo "🔄 Setting up new port forwarding..."
    powershell.exe -Command "Start-Process powershell -ArgumentList 'netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8080 connectaddress=$WSL_IP connectport=8080' -Verb RunAs"

    echo "✅ Port forwarding updated for WSL2 IP: $WSL_IP"
fi

# 4️⃣ 실행할 Docker Compose 파일 확인
COMPOSE_FILE="docker-compose.yaml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: $COMPOSE_FILE not found! Please check the path."
    exit 1
fi

# 5️⃣ Docker Compose 실행
echo "🐳 Running Docker Compose..."
docker compose --env-file ../.env up --build --remove-orphans

echo "✅ Airflow is now running! Access it at: http://localhost:8080"
