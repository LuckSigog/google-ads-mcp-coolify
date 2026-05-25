FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clones the upstream MCP server and copies into /app
RUN git clone https://github.com/gomarble-ai/google-ads-mcp-server.git /tmp/upstream \
    && cp -r /tmp/upstream/. /app/ \
    && rm -rf /tmp/upstream

# Patch hardcoded v19 (deprecated by Google) -> v20 in upstream files
RUN sed -i 's|v19|v20|g' /app/server.py /app/oauth/google_auth.py

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "uvicorn[standard]"

# Wrapper: HTTP transport + optional Bearer auth + env-var credentials bootstrap
COPY entrypoint.py /app/entrypoint.py

ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_ADS_AUTH_TYPE=oauth
ENV GOOGLE_ADS_CREDENTIALS_PATH=/app/credentials/credentials.json

EXPOSE 8000

CMD ["python", "/app/entrypoint.py"]
