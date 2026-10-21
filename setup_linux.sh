#!/usr/bin/env bash
# Miller's Jarvis — one-time setup for Linux / WSL2
set -e
cd "$(dirname "$0")"

echo "== Step 1/3: Python check =="
python3 --version || { echo "Python 3 install karo pehle (python.org)"; exit 1; }

echo "== Step 2/3: Ollama =="
if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama install ho raha hai..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "Ollama already installed."
fi

echo "== Step 3/3: Model download (qwen3.5:4b, ~2.6 GB, one time) =="
ollama pull qwen3.5:4b

echo ""
echo "Setup done! Jarvis chalane ke liye:"
echo "  python3 jarvis.py"
