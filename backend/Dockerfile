FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies (optimization for free tier)
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Lightweight healthcheck for free tier
HEALTHCHECK --interval=60s --timeout=10s --retries=2 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
