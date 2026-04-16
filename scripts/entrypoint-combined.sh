#!/bin/bash
set -e

echo "Starting Text2SQL Agent (Combined Mode)..."

# Start FastAPI in background
echo "Starting FastAPI on port 8000..."
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Wait briefly for FastAPI to start
sleep 2

# Check if FastAPI is running
if ! kill -0 $UVICORN_PID 2>/dev/null; then
    echo "ERROR: FastAPI failed to start"
    exit 1
fi

echo "FastAPI started successfully (PID: $UVICORN_PID)"

# Start Streamlit in foreground
echo "Starting Streamlit on port 8501..."
exec streamlit run app/ui/streamlit_app.py --server.port=8501 --server.address=0.0.0.0