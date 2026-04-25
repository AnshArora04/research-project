"""FastAPI server for the PPD Explorer.

Serves the React/HTML design bundle from web/static/ verbatim. Real data
is baked into web/static/ppd-data.js by web/bake_data.py.

All static assets are served with `Cache-Control: no-store` so changes to
the JSX/JS bundle reach the browser on the next reload. The Babel runtime
in index.html otherwise caches transpiled JSX aggressively.

Run:  uvicorn web.server:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

STATIC_DIR = Path(__file__).resolve().parent / "static"

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


class NoCacheStaticFiles(StaticFiles):
    """StaticFiles subclass that adds no-cache headers to every response."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        for k, v in NO_CACHE_HEADERS.items():
            response.headers[k] = v
        return response


app = FastAPI(title="PPD Explorer", docs_url=None, redoc_url=None)

app.mount("/static", NoCacheStaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", headers=NO_CACHE_HEADERS)


@app.get("/health", include_in_schema=False)
def health() -> dict:
    data_js = STATIC_DIR / "ppd-data.js"
    return {
        "ok": True,
        "data_baked": data_js.exists(),
        "data_size_bytes": data_js.stat().st_size if data_js.exists() else 0,
    }
