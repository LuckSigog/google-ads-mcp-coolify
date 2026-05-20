"""HTTP wrapper for gomarble-ai/google-ads-mcp-server.

Features added on top of upstream:
  1. Streamable HTTP transport (default upstream uses stdio, useless for remote MCP).
  2. Optional Bearer token auth via `MCP_AUTH_TOKEN` env var (Phase 1: shared token).
  3. Bootstrap of `credentials.json` from `GOOGLE_ADS_CREDENTIALS_JSON` env var,
     so a Coolify File Mount is no longer required.
"""
import os
import sys

sys.path.insert(0, "/app")

# --- Bootstrap credentials.json from env var (Coolify-friendly) ----------------
_creds_json = os.environ.get("GOOGLE_ADS_CREDENTIALS_JSON")
_creds_path = os.environ.get(
    "GOOGLE_ADS_CREDENTIALS_PATH", "/app/credentials/credentials.json"
)
if _creds_json:
    os.makedirs(os.path.dirname(_creds_path), exist_ok=True)
    with open(_creds_path, "w") as _f:
        _f.write(_creds_json)
    print(
        f"[entrypoint] credentials.json bootstrapped from env -> {_creds_path}",
        flush=True,
    )

from server import mcp  # noqa: E402


# --- Bearer auth middleware ----------------------------------------------------
class BearerAuthMiddleware:
    """Requires `Authorization: Bearer <MCP_AUTH_TOKEN>` on all HTTP requests."""

    def __init__(self, app, expected_token: str):
        self.app = app
        self.expected = expected_token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth = headers.get(b"authorization", b"").decode("latin-1")
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""

        if token != self.expected:
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"www-authenticate", b'Bearer realm="mcp"'),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"error":"unauthorized"}',
            })
            return

        await self.app(scope, receive, send)


def _get_starlette_app():
    """Return FastMCP's underlying Starlette ASGI app for streamable-http."""
    if hasattr(mcp, "streamable_http_app"):
        return mcp.streamable_http_app()
    if hasattr(mcp, "http_app"):
        return mcp.http_app()
    raise RuntimeError(
        "FastMCP instance exposes neither streamable_http_app() nor http_app(). "
        "Upgrade fastmcp (>=2.0) or check upstream gomarble server.py."
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    auth_token = (os.environ.get("MCP_AUTH_TOKEN") or "").strip() or None

    if auth_token:
        print("[entrypoint] Bearer auth ENABLED.", flush=True)
        app = BearerAuthMiddleware(_get_starlette_app(), auth_token)
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    else:
        print(
            "[entrypoint] WARNING: MCP_AUTH_TOKEN not set. "
            "Endpoint is PUBLICLY UNAUTHENTICATED.",
            file=sys.stderr,
            flush=True,
        )
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
