#!/bin/bash

# Flight Looker Docker Runner
# Usage: ./docker-run.sh [command] [args...]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Flight Looker Docker Runner ===${NC}\n"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Build image if needed
if [[ "$(docker images -q flight-looker:latest 2> /dev/null)" == "" ]]; then
    echo -e "${GREEN}Building Docker image...${NC}"
    docker build -t flight-looker:latest .
fi

# Parse command
if [ "$1" == "login" ]; then
    echo -e "${GREEN}Logging into NordVPN...${NC}"
    docker run -it --rm \
        --cap-add=NET_ADMIN \
        --device /dev/net/tun \
        flight-looker:latest \
        nordvpn login

elif [ "$1" == "shell" ]; then
    echo -e "${GREEN}Starting interactive shell...${NC}"
    docker run -it --rm \
        --cap-add=NET_ADMIN \
        --device /dev/net/tun \
        -v "$(pwd)/.env:/app/.env:ro" \
        -v "$(pwd)/charts:/app/charts" \
        -v "$(pwd)/data:/app/data" \
        flight-looker:latest \
        /bin/bash

elif [ "$1" == "top-deals" ]; then
    shift
    echo -e "${GREEN}Running top_deals.py...${NC}"
    docker run -it --rm \
        --cap-add=NET_ADMIN \
        --device /dev/net/tun \
        -v "$(pwd)/.env:/app/.env:ro" \
        -v "$(pwd)/charts:/app/charts" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/.exchange_rates_cache.json:/app/.exchange_rates_cache.json" \
        flight-looker:latest \
        python3 top_deals.py "$@"

elif [ "$1" == "main" ]; then
    shift
    echo -e "${GREEN}Running main.py...${NC}"
    docker run -it --rm \
        --cap-add=NET_ADMIN \
        --device /dev/net/tun \
        -v "$(pwd)/.env:/app/.env:ro" \
        -v "$(pwd)/charts:/app/charts" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/.exchange_rates_cache.json:/app/.exchange_rates_cache.json" \
        flight-looker:latest \
        python3 main.py "$@"

else
    echo "Usage: ./docker-run.sh [command] [args...]"
    echo ""
    echo "Commands:"
    echo "  login              - Login to NordVPN"
    echo "  shell              - Start interactive bash shell"
    echo "  top-deals [args]   - Run top_deals.py with arguments"
    echo "  main [args]        - Run main.py with arguments"
    echo ""
    echo "Examples:"
    echo "  ./docker-run.sh login"
    echo "  ./docker-run.sh top-deals --origin WAW --destination BCN --date 2026-03-15"
    echo "  ./docker-run.sh main --origin POZ --destination AMS --countries poland germany --use-vpn"
fi
