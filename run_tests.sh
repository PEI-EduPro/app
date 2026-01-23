#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Test Suite Setup...${NC}"

# 1. Start Infrastructure
echo -e "${GREEN}1. Starting Docker Services (DB & Keycloak)...${NC}"
# Use the dev compose file. '-d' for detached. '--wait' waits for healthchecks if defined, 
# but we might not have healthchecks defined for all, so we'll add a manual wait just in case.
docker compose -f deployment/docker-compose.dev.yml up -d

# Wait specifically for Keycloak to be responsive
echo "Waiting for Keycloak to be ready..."
# Loop checking the health endpoint or just port open
timeout=60
counter=0
while ! curl -s http://localhost:8080/health > /dev/null; do
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
# Run integration tests (connects to Docker services)
PYTHONPATH=. uv run pytest tests/integration

echo -e "${GREEN}All tests passed successfully!${NC}"
