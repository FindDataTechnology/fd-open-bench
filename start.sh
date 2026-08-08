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

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -e ".[dev]"

# Run database migrations (SQLite file is created automatically)
echo "Running database migrations..."
alembic upgrade head

# Export Vite env vars
export VITE_API_URL="${API_URL:-http://localhost:8999}"

# Start backend server
echo "Starting FastAPI backend on http://localhost:${FASTAPI_PORT:-8999}..."
uvicorn app.main:app --reload --host ${FASTAPI_HOST:-0.0.0.0} --port ${FASTAPI_PORT:-8999} &
BACKEND_PID=$!

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
wait $BACKEND_PID $FRONTEND_PID
