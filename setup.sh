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
  echo "Node.js is required for the frontend. Install Node 18 or newer, then run: cd frontend && npm install"
else
  cd frontend
  npm install
  cd ..
fi

mkdir -p outputs/sessions outputs/reports models

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if command -v ollama >/dev/null 2>&1; then
  echo "Ollama found. Recommended starter model:"
  echo "  ollama pull qwen3:4b"
else
  echo "Ollama is optional but recommended. Install it from https://ollama.com"
fi

echo ""
echo "Setup complete."
echo "Run backend:  source .venv/bin/activate && uvicorn backend.main:app --reload"
echo "Run frontend: cd frontend && npm run dev"
