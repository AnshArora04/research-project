"""FastAPI server for the PPD Explorer.

Serves the React/HTML design bundle from web/static/ verbatim. Real data
is baked into web/static/ppd-data.js by web/bake_data.py.

Run:  uvicorn web.server:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="PPD Explorer", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", include_in_schema=False)
def health() -> dict:
    data_js = STATIC_DIR / "ppd-data.js"
    return {
        "ok": True,
        "data_baked": data_js.exists(),
        "data_size_bytes": data_js.stat().st_size if data_js.exists() else 0,
    }
