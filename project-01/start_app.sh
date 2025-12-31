#!/bin/bash

# Legal Chatbot Startup Script for Linux/WSL
# Optimized for WSL Networking & Tailscale Security

# Exit on error
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
MODEL_NAME="phi3"

echo "----------------------------------------"
echo "Starting Legal Chatbot..."
echo "----------------------------------------"

# 1. Get Tailscale IP
echo "Detecting Tailscale IP..."
if command -v tailscale &> /dev/null; then
    TAILSCALE_IP=$(tailscale ip -4 | head -n 1)
else
    TAILSCALE_IP=$(powershell.exe -Command "tailscale ip -4" 2>/dev/null | head -n 1 | tr -d '\r')
fi

if [ -z "$TAILSCALE_IP" ]; then
    TAILSCALE_IP="[Not Found]"
fi

# 2. Handle Ollama (Internal Only)
echo "Checking Ollama status..."
if ! curl -s "http://localhost:11434/api/tags" > /dev/null; then
    echo "Ollama is not running. Starting it internally..."
    if command -v ollama &> /dev/null; then
        export OLLAMA_HOST="127.0.0.1:11434"
        ollama serve > /tmp/ollama_wsl.log 2>&1 &
        echo "Waiting for Ollama to initialize..."
        for i in {1..10}; do
            if curl -s "http://localhost:11434/api/tags" > /dev/null; then
                break
            fi
            sleep 2
        done
    fi
fi

# 3. Check and Pull Model
if curl -s "http://localhost:11434/api/tags" > /dev/null; then
    if ! ollama list | grep -q "$MODEL_NAME"; then
        echo "Model '$MODEL_NAME' missing. Pulling..."
        ollama pull "$MODEL_NAME"
    fi
fi

# 4. Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
fi

# 5. WSL Compatibility
VENV_DIR="$SCRIPT_DIR/venv"
if [[ "$SCRIPT_DIR" == /mnt/* ]]; then
    VENV_DIR="$HOME/.venvs/legal_chatbot_project01"
    mkdir -p "$HOME/.venvs"
fi

# 6. Check/Create venv
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    [ -d "$VENV_DIR" ] && rm -rf "$VENV_DIR"
    $PYTHON_CMD -m venv "$VENV_DIR" --copies
fi

# 7. Activate and Start Server
source "$VENV_DIR/bin/activate"
pip install -r requirements.txt > /dev/null 2>&1

echo "----------------------------------------"
echo "SERVER IS LIVE"
echo "On this machine: http://localhost:8000"
echo "Via Tailscale:   http://$TAILSCALE_IP:8000"
echo "----------------------------------------"

# Bind to 0.0.0.0 for WSL compatibility
python -m uvicorn main:app --host 0.0.0.0 --port 8000
