# Google Ads MCP Server — Self-Hosted on Coolify (Docker, HTTP/SSE)

> Deploy the **Google Ads MCP Server** on your own VPS with **Coolify** in 5 minutes. Connects **Claude Code**, **Claude Desktop**, **Cursor**, or any Model Context Protocol client to the **Google Ads API** via OAuth 2.0 — over HTTPS, with a public endpoint.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](./Dockerfile)
[![Coolify](https://img.shields.io/badge/Coolify-compatible-8B5CF6)](https://coolify.io)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-streamable--http-FF6B6B)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)

This repo is a **production-ready Docker wrapper** around [`gomarble-ai/google-ads-mcp-server`](https://github.com/gomarble-ai/google-ads-mcp-server) that solves the two missing pieces for remote deployment:

1. **No Dockerfile upstream** → this repo adds one.
2. **Upstream runs in `stdio` mode** (only works locally with Claude Desktop) → this repo wraps it with `streamable-http` transport so it can be reached over the internet.

Perfect for teams running self-hosted MCP infrastructure on platforms like **Coolify**, **Dokploy**, **EasyPanel**, **Railway**, **Render**, **Fly.io**, or any plain Docker/Kubernetes setup.

---

## Table of contents

- [Why self-host a Google Ads MCP server?](#why-self-host-a-google-ads-mcp-server)
- [Features](#features)
- [How it works](#how-it-works)
- [Quick start (Coolify)](#quick-start-coolify)
- [Quick start (plain Docker)](#quick-start-plain-docker)
- [Generating the OAuth credentials.json](#generating-the-oauth-credentialsjson)
- [Connecting from Claude Code / Cursor / Claude Desktop](#connecting-from-claude-code--cursor--claude-desktop)
- [Available MCP tools](#available-mcp-tools)
- [Security notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Why self-host a Google Ads MCP server?

- **Privacy**: your Google Ads OAuth tokens never leave your infrastructure.
- **Multi-client**: one deployed instance serves Claude Code, Cursor, Continue, Zed, n8n, and any other MCP-compatible tool.
- **No paid SaaS gateway**: skip third-party MCP relays — go straight from your AI client to your VPS to the Google Ads API.
- **Works behind reverse proxies**: HTTPS via Let's Encrypt, custom subdomain, optional auth middleware.

## Features

- ✅ **Streamable HTTP transport** (MCP spec) — works with all modern MCP clients
- ✅ **OAuth 2.0** with auto refresh — no manual token rotation
- ✅ **Single subdomain deploy** — `https://google-ads-mcp.yourdomain.com/mcp`
- ✅ **Multi-account / MCC support** via `GOOGLE_ADS_LOGIN_CUSTOMER_ID`
- ✅ **Built on FastMCP** — fast, async, production-grade
- ✅ **Up-to-date upstream**: each build pulls the latest `gomarble-ai/google-ads-mcp-server` from `main`
- ✅ **Coolify-tested** — also runs on Dokploy, EasyPanel, Railway, Fly.io, plain Docker

## How it works

```
┌─────────────────┐       HTTPS         ┌────────────────────────┐       OAuth        ┌──────────────────┐
│  Claude Code /  │ ──── /mcp ─────────▶│  This container        │ ──── refresh ────▶ │  Google Ads API  │
│  Cursor / etc.  │                     │  (FastMCP HTTP server) │                    │  (v19)           │
└─────────────────┘                     └────────────────────────┘                    └──────────────────┘
                                                  │
                                                  ▼
                                        /app/credentials/credentials.json
                                        (mounted as a file by Coolify)
```

The container does three things at startup:

1. Loads OAuth tokens from `/app/credentials/credentials.json` (file mount).
2. Imports the FastMCP app defined in the upstream `server.py`.
3. Runs it on `0.0.0.0:8000` using `streamable-http` transport.

---

## Quick start (Coolify)

### 1. Point a subdomain to your VPS

| Type | Name | Value |
|---|---|---|
| A | `google-ads-mcp` | `<your VPS IP>` |

### 2. Create the resource

**Coolify → + New Resource → Public Repository**

| Field | Value |
|---|---|
| Repository | `https://github.com/LuckSigog/google-ads-mcp-coolify` |
| Branch | `main` |
| Build Pack | Dockerfile |
| Dockerfile Location | `/Dockerfile` |
| Port Exposed | `8000` |
| Domain | `https://google-ads-mcp.yourdomain.com` |

### 3. Environment Variables

```env
GOOGLE_ADS_DEVELOPER_TOKEN=<your_developer_token>
GOOGLE_ADS_AUTH_TYPE=oauth
GOOGLE_ADS_CREDENTIALS_PATH=/app/credentials/credentials.json
PORT=8000

# Optional — only if you use a Manager (MCC) account:
# GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
```

> ⚠️ **Do not** set `NODE_ENV` or any unrelated env var — Coolify injects all env vars as build ARGs, which can break unrelated builds.

### 4. Mount the OAuth credentials

**Coolify → Storages → + Add → File Mount**

| Mount Path | Content |
|---|---|
| `/app/credentials/credentials.json` | Paste the entire JSON generated below |

### 5. Deploy

Click **Deploy**. When the container is healthy:

```bash
curl -i https://google-ads-mcp.yourdomain.com/mcp
# Expected: HTTP 200, 405, or similar — NOT 502
```

---

## Quick start (plain Docker)

```bash
docker build -t google-ads-mcp .

docker run -d \
  --name google-ads-mcp \
  -p 8000:8000 \
  -e GOOGLE_ADS_DEVELOPER_TOKEN=your_token \
  -e GOOGLE_ADS_AUTH_TYPE=oauth \
  -e GOOGLE_ADS_CREDENTIALS_PATH=/app/credentials/credentials.json \
  -v $(pwd)/credentials.json:/app/credentials/credentials.json:ro \
  google-ads-mcp
```

---

## Generating the OAuth `credentials.json`

You only run this **once on your local machine** to bootstrap the refresh token. The container will refresh access tokens automatically from then on.

### Prerequisites

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create an **OAuth 2.0 Client ID** of type **Desktop application**
3. Download the `client_secret_*.json` file
4. Make sure the [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com) is enabled in the project
5. Have a **Google Ads Developer Token** ([apply here](https://ads.google.com/aw/apicenter))

### Run the bootstrap script

```python
# gen_credentials.py
from google_auth_oauthlib.flow import InstalledAppFlow
import json, glob, sys

matches = glob.glob('client_secret*.json')
if not matches:
    sys.exit("Place a client_secret*.json next to this script first.")

flow = InstalledAppFlow.from_client_secrets_file(
    matches[0], scopes=['https://www.googleapis.com/auth/adwords'])
creds = flow.run_local_server(port=0)

with open('credentials.json', 'w') as f:
    json.dump({
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes,
    }, f, indent=2)
print("OK -> credentials.json generated")
```

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install google-auth-oauthlib
python3 gen_credentials.py
```

A browser will open. Sign in with the Google account that has access to your Google Ads account and authorize. You'll get a `credentials.json` in the current directory.

**Upload that JSON as a File Mount on Coolify** (step 4 above).

---

## Connecting from Claude Code / Cursor / Claude Desktop

### Claude Code (CLI)

```bash
claude mcp add --transport http google-ads https://google-ads-mcp.yourdomain.com/mcp --scope user
claude mcp list
```

Test it:
```
"List my Google Ads accounts"
```

### Cursor / Continue / Zed

Add to your MCP servers config:

```json
{
  "mcpServers": {
    "google-ads": {
      "type": "http",
      "url": "https://google-ads-mcp.yourdomain.com/mcp"
    }
  }
}
```

### Claude Desktop (local stdio only)

Claude Desktop doesn't speak HTTP MCP. If you want it there, install the upstream [`gomarble-ai/google-ads-mcp-server`](https://github.com/gomarble-ai/google-ads-mcp-server) directly on your machine.

---

## Available MCP tools

Inherited from upstream:

| Tool | Description |
|---|---|
| `list_accounts` | Lists all accessible Google Ads accounts, including nested sub-accounts under MCC |
| `run_gaql` | Executes any Google Ads Query Language (GAQL) query — campaigns, ad groups, keywords, conversions, reports |
| `run_keyword_planner` | Generates keyword ideas with search volume, competition, and CPC bid range |

GAQL reference is exposed as an MCP resource: `gaql://reference`.

---

## Security notes

The default deploy exposes the MCP endpoint to the public internet without authentication. **Anyone who guesses the URL can query your Google Ads data.** Recommended hardening:

- **Basic Auth** via Traefik middleware in Coolify (1-line label on the service).
- **Bearer token check** in a reverse proxy or with a tiny FastAPI middleware in front of `entrypoint.py`.
- **IP allowlist** at the Coolify/Cloudflare level if you connect from a fixed set of dev machines.
- **Cloudflare Access / Tailscale / WireGuard** if you want SSO or zero-trust.

PRs adding optional `MCP_AUTH_TOKEN` header validation are welcome.

---

## Troubleshooting

### `sh: tsc: not found` or build fails with missing devDependencies
You're hitting the Coolify env-var-as-build-ARG quirk. **Don't set `NODE_ENV=production` as an env var on the Coolify service.** That gets injected as a build ARG and breaks unrelated Dockerfiles. (This repo is Python, but the same pattern bites Node-based MCP servers.)

### `ERROR: failed to read dockerfile`
Check **Base Directory = `/`** and **Dockerfile Location = `/Dockerfile`** in the Coolify Configuration tab.

### `401 Unauthorized` / `OAuth credentials expired`
Open `credentials.json` and confirm `refresh_token` is present. If it's missing, regenerate via `gen_credentials.py` and re-upload the file mount.

### `Developer token is not approved`
A fresh developer token has limited access (test accounts only). For production accounts, apply for **Basic Access** in the [Google Ads API Center](https://ads.google.com/aw/apicenter).

### `LOGIN_CUSTOMER_ID required`
You're querying through a Manager (MCC) account. Set `GOOGLE_ADS_LOGIN_CUSTOMER_ID=<mcc_id_without_dashes>` and redeploy.

### `502 Bad Gateway` after deploy
Container started but isn't listening on port 8000. Check the build logs — most often the `git clone` of upstream failed. Re-trigger the deploy.

---

## Contributing

PRs welcome. Specifically useful:

- Optional auth middleware (Bearer / Basic / IP allowlist)
- Pinned upstream SHA option (currently builds against `main`)
- Helm chart / Kubernetes manifests
- Examples for n8n, Make, Zapier MCP integrations

## License

[MIT](./LICENSE) — same license as the upstream gomarble project.

## Credits

- Upstream MCP server: [gomarble-ai/google-ads-mcp-server](https://github.com/gomarble-ai/google-ads-mcp-server)
- Model Context Protocol: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- Coolify: [coolify.io](https://coolify.io)
- FastMCP: [jlowin/fastmcp](https://github.com/jlowin/fastmcp)

---

**Keywords**: google ads mcp server, google ads mcp coolify, self-hosted mcp google ads, mcp server docker, deploy mcp server vps, claude code google ads integration, fastmcp http server, google ads api claude, mcp streamable http, model context protocol google ads, cursor google ads mcp, n8n google ads mcp, self host model context protocol, google ads oauth mcp.
