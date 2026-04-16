# Text2SQL Agent Dockerfile
# Multi-service: Streamlit UI + FastAPI backend

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Copy and setup entrypoint script for combined mode
COPY scripts/entrypoint-combined.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create runtime directories (.deploy/ for ephemeral data)
RUN mkdir -p .deploy/chroma .deploy/logs

# Expose ports
# 8501: Streamlit UI
# 8000: FastAPI backend
EXPOSE 8501 8000

# Default environment
ENV APP_ENV=production \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    PYTHONUNBUFFERED=1

# Default command: combined mode (FastAPI + Streamlit)
CMD ["/app/entrypoint.sh"]