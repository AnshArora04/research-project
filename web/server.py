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

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.types import Scope

from web.analysis import (
    get_variables,
    run_correlation,
    run_group_comparison,
    run_ols,
    run_univariate,
)

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


@app.get("/api/analysis/variables", include_in_schema=False)
def analysis_variables() -> list[dict]:
    return get_variables()


class RunRequest(BaseModel):
    test: str
    spec: dict[str, Any] = Field(default_factory=dict)


@app.post("/api/analysis/run", include_in_schema=False)
def analysis_run(req: RunRequest) -> dict:
    spec = req.spec or {}
    try:
        if req.test == "univariate":
            return run_univariate(y=spec.get("y"), group_by=spec.get("group_by"))
        if req.test == "ols":
            return run_ols(
                y=spec.get("y"),
                xs=spec.get("xs") or [],
                controls=spec.get("controls") or [],
                fe=spec.get("fe") or [],
                weights=spec.get("weights") or "equal",
                cluster=spec.get("cluster") or "entity",
            )
        if req.test == "group_comparison":
            return run_group_comparison(
                y=spec.get("y"),
                group_a=spec.get("group_a") or {},
                group_b=spec.get("group_b") or {},
            )
        if req.test == "correlation":
            return run_correlation(
                vars_list=spec.get("vars") or [],
                scatter_pair=spec.get("scatter_pair"),
            )
        raise HTTPException(status_code=400, detail=f"Unknown test {req.test!r}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
