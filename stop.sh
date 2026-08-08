#!/bin/bash

echo "Stopping fd-open-bench development environment..."

# Kill background processes
pkill -f "uvicorn app.main:app" 2>/dev/null || true

echo "Stopped backend."

# Optional: Stop Docker containers (if running)
if docker-compose -f docker-compose.yml ps 2>/dev/null | grep -q up; then
    echo "Stopping Docker containers..."
    docker-compose -f docker-compose.yml down
fi

echo "Development environment stopped."
