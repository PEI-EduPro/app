#!/bin/bash
set -e

cd "$(dirname "$0")"

if docker volume inspect edupro_keycloak_db_data &>/dev/null; then
    docker compose up -d --build
else
    echo "First deploy: running with setup profile..."
    docker compose --profile setup up -d --build
fi
