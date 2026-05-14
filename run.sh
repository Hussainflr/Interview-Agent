#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Starting Interview Agent with integrated LobeChat frontend..."

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
fi

generate_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 32
  else
    python3 - <<'PY'
import base64
import os
print(base64.b64encode(os.urandom(32)).decode())
PY
  fi
}

ensure_env_secret() {
  local name="$1"
  local current=""
  if [ -f ".env" ]; then
    current="$(grep -E "^${name}=" .env | tail -n 1 | cut -d= -f2- || true)"
  fi
  if [ -z "$current" ]; then
    echo "${name}=$(generate_secret)" >> .env
    echo "Generated ${name} in .env"
  fi
}

ensure_env_secret "KEY_VAULTS_SECRET"
ensure_env_secret "AUTH_SECRET"

ensure_env_value() {
  local name="$1"
  local value="$2"
  local current=""
  if [ -f ".env" ]; then
    current="$(grep -E "^${name}=" .env | tail -n 1 | cut -d= -f2- || true)"
  fi
  if [ -z "$current" ]; then
    echo "${name}=${value}" >> .env
    echo "Set ${name} in .env"
  fi
}

ensure_env_value "LOBE_DB_NAME" "lobechat"
ensure_env_value "LOBE_POSTGRES_PORT" "54322"
ensure_env_value "POSTGRES_PASSWORD" "interview-local-postgres"

set -a
source .env
set +a

if ! command -v pnpm >/dev/null 2>&1; then
  if command -v corepack >/dev/null 2>&1; then
    corepack enable
  else
    echo "pnpm is required for the integrated LobeChat frontend."
    echo "Install it with: npm install -g pnpm"
    exit 1
  fi
fi

mkdir -p outputs/sessions outputs/reports outputs/audit

if [ -z "${DATABASE_URL:-}" ]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "LobeChat source mode needs DATABASE_URL. Install Docker Desktop so ./run.sh can start local Postgres,"
    echo "or set DATABASE_URL in .env to an existing Postgres database."
    exit 1
  fi

  echo "Starting local LobeChat Postgres on port ${LOBE_POSTGRES_PORT:-54322}"
  docker compose -f docker-compose.lobechat.yml up -d lobechat-postgres

  echo "Waiting for Postgres..."
  for _ in $(seq 1 40); do
    if docker compose -f docker-compose.lobechat.yml exec -T lobechat-postgres pg_isready -U postgres >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  export DATABASE_DRIVER=node
  export DATABASE_URL="postgresql://postgres:${POSTGRES_PASSWORD}@127.0.0.1:${LOBE_POSTGRES_PORT}/${LOBE_DB_NAME}"
fi

if docker compose -f docker-compose.lobechat.yml exec -T lobechat-postgres psql -U postgres -d "${LOBE_DB_NAME}" -tAc "SELECT 1 FROM pg_available_extensions WHERE name='pg_search'" 2>/dev/null | grep -q 1; then
  :
else
  echo "LobeChat Postgres is missing pg_search. Recreating local database with ParadeDB image..."
  docker compose -f docker-compose.lobechat.yml down lobechat-postgres >/dev/null 2>&1 || true
  rm -rf outputs/lobechat-postgres
  docker compose -f docker-compose.lobechat.yml up -d lobechat-postgres
  for _ in $(seq 1 40); do
    if docker compose -f docker-compose.lobechat.yml exec -T lobechat-postgres pg_isready -U postgres >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

cleanup() {
  echo ""
  echo "Stopping app..."
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

echo "Starting backend at http://127.0.0.1:8000"
"$PYTHON" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

sleep 2

if [ ! -d "frontend/node_modules" ]; then
  echo "Installing LobeChat frontend dependencies. This can take a while..."
  pnpm --dir frontend install
fi

echo "Applying LobeChat database migrations..."
(
  cd frontend
  DATABASE_DRIVER="${DATABASE_DRIVER:-node}" \
  DATABASE_URL="${DATABASE_URL}" \
  KEY_VAULTS_SECRET="${KEY_VAULTS_SECRET}" \
  AUTH_SECRET="${AUTH_SECRET}" \
  pnpm run db:migrate
)

echo "Starting LobeChat frontend at http://localhost:3010"
(
  cd frontend
  DATABASE_DRIVER="${DATABASE_DRIVER:-node}" \
  DATABASE_URL="${DATABASE_URL}" \
  KEY_VAULTS_SECRET="${KEY_VAULTS_SECRET}" \
  AUTH_SECRET="${AUTH_SECRET}" \
  ENABLED_OPENAI=1 \
  OPENAI_API_KEY="${LOBE_OPENAI_API_KEY:-interview-local-key}" \
  OPENAI_PROXY_URL="${LOBE_OPENAI_PROXY_URL:-http://127.0.0.1:8000/v1}" \
  OPENAI_MODEL_LIST="${LOBE_OPENAI_MODEL_LIST:--all,+interview-agent-local=Interview Coach,+interview-agent-hybrid=Interview Coach Hybrid}" \
  ENABLED_OLLAMA=1 \
  OLLAMA_PROXY_URL="${LOBE_OLLAMA_PROXY_URL:-http://127.0.0.1:11434}" \
  pnpm run dev:next
) &
FRONTEND_PID=$!

echo ""
echo "App is running:"
echo "  LobeChat frontend: http://localhost:3010"
echo "  Backend API:        http://127.0.0.1:8000"
echo ""
echo "Select the Interview Coach model in LobeChat."
echo "Press Ctrl+C to stop everything."

wait "$BACKEND_PID" "$FRONTEND_PID"
