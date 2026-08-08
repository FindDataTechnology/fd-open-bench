#!/bin/bash

set -e

echo "Starting fd-open-bench development environment..."

# Load environment variables from .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo ".env file created. Please configure your settings."
    exit 0
fi

# Start PostgreSQL in background (if available)
if ! pg_isready -h localhost -p 5432 &>/dev/null; then
    echo "PostgreSQL is not running. Please start it first."
    exit 1
fi

# Start Redis in background (if available)
if ! redis-cli -h localhost -p 6379 ping &>/dev/null; then
    echo "Redis is not running. Please start it first."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -e ".[dev]" || pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Export Vite env vars
export VITE_API_URL="${API_URL:-http://localhost:8999}"

# Start backend server
echo "Starting FastAPI backend on http://localhost:${FASTAPI_PORT:-8999}..."
uvicorn app.main:app --reload --host ${FASTAPI_HOST:-0.0.0.0} --port ${FASTAPI_PORT:-8999} &
BACKEND_PID=$!

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A app.celery_worker worker --loglevel=info &
WORKER_PID=$!

# Start Celery beat in background
echo "Starting Celery Beat..."
celery -A app.celery_worker beat --loglevel=info &
BEAT_PID=$!

# Start frontend
echo "Starting frontend on http://localhost:${FRONTEND_PORT:-3118}..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "Development environment is ready!"
echo "=========================================="
echo "Backend API:  http://localhost:${FASTAPI_PORT:-8999}"
echo "Swagger docs: http://localhost:${FASTAPI_PORT:-8999}/docs"
echo "Frontend:     http://localhost:${FRONTEND_PORT:-3118}"
echo "=========================================="
echo "Press Ctrl+C to stop all services"
echo "=========================================="

# Wait for processes
wait $BACKEND_PID $WORKER_PID $BEAT_PID $FRONTEND_PID
