FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OPENCLAW_HOME=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x .openclaw/scripts/*.sh \
    && chmod +x setup.sh

# Create necessary directories
RUN mkdir -p \
    .openclaw/logs \
    memory/daily \
    memory/projects \
    memory/core \
    research/papers \
    research/summaries \
    research/daily

# Set up non-root user for security
RUN useradd -m -u 1000 openclaw && \
    chown -R openclaw:openclaw /app
USER openclaw

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('.openclaw/core') else 1)" || exit 1

# Default command
CMD ["python", "-m", "openclaw.cli"]
