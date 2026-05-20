FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clona o servidor do gomarble e copia tudo pro /app
RUN git clone https://github.com/gomarble-ai/google-ads-mcp-server.git /tmp/upstream \
    && cp -r /tmp/upstream/. /app/ \
    && rm -rf /tmp/upstream

RUN pip install --no-cache-dir -r requirements.txt

# Wrapper que troca stdio por HTTP (streamable-http)
COPY entrypoint.py /app/entrypoint.py

ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_ADS_AUTH_TYPE=oauth
ENV GOOGLE_ADS_CREDENTIALS_PATH=/app/credentials/credentials.json

EXPOSE 8000

CMD ["python", "/app/entrypoint.py"]
