#!/bin/bash

# Activate the virtual environment
source backend/venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || echo "Warning: Virtual environment not found. Ensure dependencies are installed globally or adjust path."

# Read port from environment variable, default to 8000
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

# Start FastAPI server with Uvicorn
echo "Starting FastAPI server on $HOST:$PORT with 2 workers..."
python -m uvicorn backend.main:app --host $HOST --port $PORT --workers 2
