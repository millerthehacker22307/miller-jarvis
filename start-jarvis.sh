#!/usr/bin/env bash
# Miller's Jarvis - one-click launcher (Linux / WSL2 / Mac)
# Bas chalao:  bash start-jarvis.sh   — koi command alag se nahi.
set -e
cd "$(dirname "$0")"

command -v python3 >/dev/null 2>&1 || { echo "Python 3 chahiye — python.org se install karo."; exit 1; }

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama install ho raha hai..."
  curl -fsSL https://ollama.com/install.sh | sh
fi

if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama start ho raha hai..."
  (ollama serve >/dev/null 2>&1 &)
  sleep 4
fi

if ! ollama list | grep -q "qwen3.5:4b"; then
  echo "Pehli baar model download hoga (~2.6 GB)..."
  ollama pull qwen3.5:4b
fi

echo "Jarvis khul raha hai..."
exec python3 app.py
