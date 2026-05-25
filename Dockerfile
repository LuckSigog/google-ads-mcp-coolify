FROM python:3.11-slim

# Cache-bust: 2026-05-25-v20-retry
ARG CACHE_BUST=20260525b

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clones the upstream MCP server and copies into /app.
RUN echo "cache-bust=$CACHE_BUST" \
    && git clone https://github.com/gomarble-ai/google-ads-mcp-server.git /tmp/upstream \
    && cp -r /tmp/upstream/. /app/ \
    && rm -rf /tmp/upstream

# Patch hardcoded v19 (deprecated by Google) -> v20 (closest supported version,
# minimizes risk of API surface changes like removed methods).
RUN sed -i 's|v19|v20|g' /app/server.py /app/oauth/google_auth.py \
    && echo "=== Verifying patch ===" \
    && grep -n "v20\|v19" /app/server.py /app/oauth/google_auth.py || true \
    && ! grep -q "v19" /app/server.py /app/oauth/google_auth.py

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "uvicorn[standard]"

COPY entrypoint.py /app/entrypoint.py

ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_ADS_AUTH_TYPE=oauth
ENV GOOGLE_ADS_CREDENTIALS_PATH=/app/credentials/credentials.json

EXPOSE 8000

CMD ["python", "/app/entrypoint.py"]
