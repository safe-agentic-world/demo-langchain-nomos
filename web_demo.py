from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import run_flow

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"

app = FastAPI(title="Northwind Retail Support Assistant")
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")


class RunRequest(BaseModel):
    task: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.post("/api/run")
def run_demo(request: RunRequest) -> dict:
    return run_flow(task=request.task)
