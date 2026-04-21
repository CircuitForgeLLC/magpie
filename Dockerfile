FROM python:3.11-slim

# System deps for Playwright + Chrome + Xvfb
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb google-chrome-stable wget gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY pyproject.toml .
COPY ../circuitforge-core /cf-core
RUN pip install --no-cache-dir -e /cf-core && \
    pip install --no-cache-dir -e .

# Install Playwright browsers
RUN playwright install chromium

COPY . .

EXPOSE 8532

CMD ["python", "-m", "app.main"]
