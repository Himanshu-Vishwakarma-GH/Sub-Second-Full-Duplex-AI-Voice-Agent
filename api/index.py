import sys
from pathlib import Path

# Add backend directory to sys.path so server.py and its dependencies resolve
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from server import app
from fastapi.responses import JSONResponse
from fastapi import Request

@app.middleware("http")
async def debug_routing_middleware(request: Request, call_next):
    # If debug query param is present, echo scope info
    if request.url.path == "/api/debug" or request.url.path == "/debug":
        return JSONResponse({
            "url_path": request.url.path,
            "raw_path": request.scope.get("raw_path", b"").decode("latin-1"),
            "root_path": request.scope.get("root_path", ""),
            "routes": [r.path for r in app.routes if hasattr(r, "path")]
        })
    response = await call_next(request)
    return response
