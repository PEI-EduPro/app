#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Test Suite Setup...${NC}"

# 1. Start Infrastructure
echo -e "${GREEN}1. Starting ISOLATED Docker Services (DB:5433 & Keycloak:8081)...${NC}"

# Define environment variables for the test run to ensure isolation
export POSTGRES_PORT=5433
export KEYCLOAK_SERVER_URL="http://localhost:8081"
# Ensure Keycloak admin uses the test port
export KEYCLOAK_Admin_URL="http://localhost:8081" 

# Use a specific project name 'edupro-test' to namespace volumes and containers
# This prevents conflict with 'edupro-dev' or 'edupro' project names.
docker compose -p edupro-test -f deployment/docker-compose.test.yml down -v

# Start services
docker compose -p edupro-test -f deployment/docker-compose.test.yml up -d

# Wait for DB (Port 5433)
echo "Waiting for Test Database (port 5433)..."
timeout=60
counter=0
while ! timeout 1 bash -c 'cat < /dev/null > /dev/tcp/localhost/5433'; do
    sleep 1
    ((counter++))
    if [ $counter -ge $timeout ]; then
        echo -e "${RED}Timeout waiting for Database!${NC}"
        exit 1
    fi
    echo -n "."
done
echo -e "\n${GREEN}Test Database is ready!${NC}"

# Wait specifically for Keycloak (Port 8081)
echo "Waiting for Test Keycloak (port 8081)..."
timeout=120
counter=0
while ! curl -s http://localhost:8081/health > /dev/null; do
    sleep 2
    ((counter+=2))
    if [ $counter -ge $timeout ]; then
        echo -e "${RED}Timeout waiting for Keycloak!${NC}"
        exit 1
    fi
    echo -n "."
done
echo -e "\n${GREEN}Infrastructure is Ready!${NC}"

# 2. Run Tests
cd api

echo -e "${GREEN}2. Running Unit Tests...${NC}"
# Run unit tests (should be fast, in-memory DB)
PYTHONPATH=. uv run pytest tests/unit

echo -e "${GREEN}3. Running Integration Tests...${NC}"
# Run integration tests (connects to ISOLATED Docker services)
# Pass env vars explicitly to ensure pytest picks them up
PYTHONPATH=. POSTGRES_PORT=5433 KEYCLOAK_SERVER_URL="http://localhost:8081" KEYCLOAK_ISSUER_URL="http://localhost:8081" uv run pytest tests/integration

echo -e "${GREEN}All tests passed successfully!${NC}"
