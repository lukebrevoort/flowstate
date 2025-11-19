#!/bin/bash
# FlowState Backend Startup Script
# Ensures the correct Python environment is used

cd "$(dirname "$0")"

echo "🚀 Starting FlowState Backend..."
echo ""

# Activate virtual environment and start uvicorn
./venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload
