#!/usr/bin/env bash
set -euo pipefail

echo "Setting up Local Interview Agent"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3.10 or newer, then rerun this script."
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required for the LobeChat frontend. Install Node 20 or newer."
else
  if ! command -v pnpm >/dev/null 2>&1; then
    if command -v corepack >/dev/null 2>&1; then
      corepack enable
    else
      echo "pnpm is required for LobeChat. Install it with: npm install -g pnpm"
      exit 1
    fi
  fi
  pnpm --dir frontend install
fi

mkdir -p outputs/sessions outputs/reports outputs/audit models

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

generate_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 32
  else
    python - <<'PY'
import base64
import os
print(base64.b64encode(os.urandom(32)).decode())
PY
  fi
}

ensure_env_secret() {
  local name="$1"
  local current=""
  current="$(grep -E "^${name}=" .env | tail -n 1 | cut -d= -f2- || true)"
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
  current="$(grep -E "^${name}=" .env | tail -n 1 | cut -d= -f2- || true)"
  if [ -z "$current" ]; then
    echo "${name}=${value}" >> .env
    echo "Set ${name} in .env"
  fi
}

ensure_env_value "LOBE_DB_NAME" "lobechat"
ensure_env_value "LOBE_POSTGRES_PORT" "54322"
ensure_env_value "POSTGRES_PASSWORD" "interview-local-postgres"

if command -v ollama >/dev/null 2>&1; then
  echo "Ollama found. Recommended starter model:"
  echo "  ollama pull qwen3:4b"
else
  echo "Ollama is optional but recommended. Install it from https://ollama.com"
fi

echo ""
echo "Setup complete."
echo "Run the full app: ./run.sh"
