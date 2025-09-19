# Cash Completeness Monitor - Docker Image

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Create directory for state file
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV STATE_STORAGE_PATH=/app/data/state.json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from main import CashCompletenessMonitor; print('OK')" || exit 1

# Default command
CMD ["python", "main.py"]

# Labels
LABEL maintainer="Platform Accounting Team"
LABEL description="Real-time automation of Customer Cash Completeness Checks"
LABEL version="1.0"