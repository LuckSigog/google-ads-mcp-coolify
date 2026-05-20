"""Wrapper que importa o FastMCP do gomarble e expoe via HTTP streamable.

O gomarble/google-ads-mcp-server termina o `server.py` com `mcp.run()` em modo
stdio (pensado pro Claude Desktop). Esse wrapper importa o objeto `mcp` ja
configurado e roda no transporte HTTP, permitindo deploy remoto (Coolify).
"""
import os
import sys

sys.path.insert(0, "/app")

from server import mcp

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
