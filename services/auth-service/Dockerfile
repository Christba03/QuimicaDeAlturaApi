# Multi-stage Dockerfile for optimized builds
# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies layer (cached unless requirements.txt changes)
FROM base as dependencies

# Copy only requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (cached layer)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Production image
FROM dependencies as production

# Copy application code (changes frequently, so last)
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

CMD ["sh", "-c", "python bootstrap_db.py && exec uvicorn src.main:app --host 0.0.0.0 --port 8001"]

# Stage 4: Development image (optional, includes dev tools)
FROM dependencies as development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio httpx black isort flake8 mypy

COPY . .

EXPOSE 8001

CMD ["sh", "-c", "python bootstrap_db.py && exec uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload"]
