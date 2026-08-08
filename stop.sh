#!/bin/bash

echo "Stopping fd-open-bench development environment..."

# Kill background processes
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true

echo "Stopped backend, Celery worker, and Celery Beat."

# Optional: Stop Docker containers (if running)
if docker-compose -f docker-compose.yml ps | grep -q up; then
    echo "Stopping Docker containers..."
    docker-compose -f docker-compose.yml down
fi

echo "Development environment stopped."
