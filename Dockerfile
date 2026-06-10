# ── Halol Crypto AI — Dockerfile ──────────────────────────────────────────────
FROM python:3.11-slim

# Metadata
LABEL maintainer="Halol Crypto AI"
LABEL description="Halal spot crypto assistant — Telegram Bot + Mini App"

# Working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data and log directories
RUN mkdir -p data logs

# Non-root user for security
RUN useradd -m -u 1000 halol && chown -R halol:halol /app
USER halol

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Default: polling + web server
# Override with: docker run ... python main.py --webhook
CMD ["python", "main.py"]
