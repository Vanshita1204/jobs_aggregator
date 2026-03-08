#!/usr/bin/env bash

# Unified dev runner for backend, frontend, Redis and Celery.
# Run from anywhere; it will cd to the repo root automatically.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "== jobs_aggregator dev stack =="

# Optionally auto-activate the local virtualenv if present and not already active
if [ -z "${VIRTUAL_ENV:-}" ] && [ -f "env/bin/activate" ]; then
    echo "Activating Python virtualenv at ./env"
    # shellcheck disable=SC1091
    source "env/bin/activate"
fi

REQUIRED_CMDS=("python" "uvicorn" "celery" "npm")

if ! command_exists redis-server; then
    echo "WARNING: 'redis-server' not found on PATH."
    echo "         Install Redis and ensure 'redis-server' is available (e.g. 'brew install redis' on macOS)."
else
    REQUIRED_CMDS+=("redis-server")
fi

for cmd in "${REQUIRED_CMDS[@]}"; do
    if ! command_exists "$cmd"; then
        echo "ERROR: Required command '$cmd' is not installed or not on PATH."
        echo "Please install all prerequisites (see README) and try again."
        exit 1
    fi
done

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo "Backend:  http://localhost:${BACKEND_PORT}"
echo "Frontend: http://localhost:${FRONTEND_PORT}"
echo "Redis:    redis://localhost:${REDIS_PORT}/0"

PIDS=()

start_backend() {
    echo "Starting FastAPI backend (uvicorn) on :${BACKEND_PORT}..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT}" &
    PIDS+=($!)
}

start_frontend() {
    echo "Starting React (Vite) frontend on :${FRONTEND_PORT}..."
    (
        cd "${ROOT_DIR}/frontend/react-app"
        # Assume dependencies were installed already (npm install).
        npm run dev -- --port "${FRONTEND_PORT}"
    ) &
    PIDS+=($!)
}

start_redis() {
    if command_exists redis-server; then
        echo "Starting Redis server on :${REDIS_PORT} (using default configuration)..."
        redis-server --port "${REDIS_PORT}" &
        PIDS+=($!)
    else
        echo "Skipping Redis server start (redis-server not available)."
    fi
}

start_celery() {
    echo "Starting Celery worker..."
    celery -A app.core.celery:celery_app worker -l info &
    PIDS+=($!)

    echo "Starting Celery beat scheduler..."
    celery -A app.core.celery:celery_app beat -l info &
    PIDS+=($!)
}

cleanup() {
    echo
    echo "Stopping dev stack..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" >/dev/null 2>&1; then
            kill "$pid" >/dev/null 2>&1 || true
        fi
    done
    wait || true
    echo "All services stopped."
}

trap cleanup INT TERM

start_redis
start_backend
start_frontend
start_celery

echo
echo "All services started."
echo "Press Ctrl+C to stop everything."

wait

