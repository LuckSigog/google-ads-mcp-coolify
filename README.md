# google-ads-mcp-coolify

Wrapper de deploy do [gomarble-ai/google-ads-mcp-server](https://github.com/gomarble-ai/google-ads-mcp-server) em modo HTTP, pronto pra rodar na Coolify.

## O que faz

- Clona o servidor do gomarble no build
- Substitui o entrypoint stdio por `streamable-http` (porta 8000)
- Espera o `credentials.json` (OAuth tokens) montado em `/app/credentials/credentials.json`

## Env vars (Coolify)

```
GOOGLE_ADS_DEVELOPER_TOKEN=<seu_dev_token>
GOOGLE_ADS_AUTH_TYPE=oauth
GOOGLE_ADS_CREDENTIALS_PATH=/app/credentials/credentials.json
PORT=8000
# Opcional, soh se tiver MCC:
# GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
```

## File Mount na Coolify

| Mount Path | Conteudo |
|---|---|
| `/app/credentials/credentials.json` | JSON gerado localmente via OAuth flow |

## Endpoint

`https://<dominio>/mcp` (streamable HTTP, padrao MCP).
