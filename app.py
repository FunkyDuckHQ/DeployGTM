"""DeployGTM sandbox web entrypoint.

Some deployment hosts auto-detect this repo as a Python app because the repo
contains operational Python scripts. This file gives those hosts an explicit
entrypoint while still serving the static dashboard.
"""

from __future__ import annotations

from pathlib import Path
from wsgiref.simple_server import make_server


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
DIST_ROOT = WEB_ROOT / "dist"
STATIC_ROOT = DIST_ROOT if DIST_ROOT.exists() else WEB_ROOT

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}


def resolve_path(raw_path: str) -> Path | None:
    path = raw_path.split("?", 1)[0] or "/"
    if path == "/":
        path = "/index.html"

    candidate = (STATIC_ROOT / path.lstrip("/")).resolve()
    try:
        candidate.relative_to(STATIC_ROOT.resolve())
    except ValueError:
        return None
    return candidate


def app(environ, start_response):
    path = resolve_path(environ.get("PATH_INFO", "/"))

    if path is None or not path.exists() or path.is_dir():
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Not found"]

    content_type = CONTENT_TYPES.get(path.suffix, "application/octet-stream")
    body = path.read_bytes()
    start_response(
        "200 OK",
        [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


if __name__ == "__main__":
    with make_server("0.0.0.0", 8000, app) as server:
        print("DeployGTM sandbox running at http://127.0.0.1:8000")
        server.serve_forever()
