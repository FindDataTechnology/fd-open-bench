#!/bin/bash

set -e

echo "Starting fd-open-bench development environment..."

# Load only the vars start.sh itself needs. We deliberately do NOT `source
# .env`: bash strips quotes, which corrupts JSON array values (CORS_ORIGINS)
# that pydantic-settings expects. The backend reads .env directly.
if [ -f .env ]; then
    export FASTAPI_PORT="$(grep -E '^FASTAPI_PORT=' .env | head -1 | cut -d= -f2- | tr -d '\"')"
    export FRONTEND_PORT="$(grep -E '^FRONTEND_PORT=' .env | head -1 | cut -d= -f2- | tr -d '\"')"
    export API_URL="$(grep -E '^API_URL=' .env | head -1 | cut -d= -f2- | tr -d '\"')"
    : "${FASTAPI_PORT:=8999}" "${FRONTEND_PORT:=3118}" "${API_URL:=http://localhost:8999}"
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
