#!/bin/bash

# 실행할 docker-compose 파일 경로
COMPOSE_FILE="./setting_object_storage/stand-alone/docker-compose.yaml"

# 해당 경로로 이동하지 않고 직접 실행
docker-compose -f "$COMPOSE_FILE" up -d
