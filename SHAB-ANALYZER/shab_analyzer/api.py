from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from . import config
from . import warehouse as wh

app = FastAPI(title="SHAB lenses", version="0.1.0")

_WAREHOUSE_PATH = config.DEFAULT_WAREHOUSE_DB


def set_warehouse_path(path: Path) -> None:
    global _WAREHOUSE_PATH
    _WAREHOUSE_PATH = Path(path)


@contextmanager
def _db():
    conn = wh.connect(_WAREHOUSE_PATH)
    try:
        yield conn
    finally:
        conn.close()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/lens/{dimension}/{key}")
def lens(
    dimension: str,
    key: str,
    mode: str = Query("timeline"),
) -> dict:
    if mode not in ("timeline", "pulse"):
        raise HTTPException(status_code=400, detail="mode must be timeline or pulse")
    try:
        with _db() as conn:
            if mode == "pulse":
                series = wh.lens_pulse(conn, dimension, key)
            else:
                series = wh.lens_timeline(conn, dimension, key)
            extra: dict = {}
            if dimension == "person" and mode == "timeline":
                extra["related_org_events"] = wh.related_org_events(conn, key)
            if dimension == "plz":
                extra["people"] = wh.plz_people(conn, key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"dimension": dimension, "key": key, "mode": mode, "series": series, **extra}
