"""FastAPI app: exposes config, run history, and a trigger endpoint for
the scraper/evaluator pipeline. Runs execute in the background so the
frontend can poll for progress instead of holding a request open.
"""

from __future__ import annotations

import os

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from src.settings import load_settings

from .db import engine, init_db
from .models import JobMatch, Run
from .runner import execute_run

app = FastAPI(title="Job Hunter API")

origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    settings = load_settings()
    return {
        "target_urls": settings.target_urls,
        "destination_email": settings.destination_email,
        "llm_model": settings.llm_model,
        "criteria": settings.criteria,
        "min_match_score": settings.min_match_score,
    }


@app.get("/api/runs")
def list_runs():
    with Session(engine) as session:
        return session.exec(select(Run).order_by(Run.started_at.desc())).all()


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        matches = session.exec(
            select(JobMatch)
            .where(JobMatch.run_id == run_id)
            .order_by(JobMatch.match_score.desc())
        ).all()
        return {"run": run, "matches": matches}


@app.post("/api/runs")
def trigger_run(background_tasks: BackgroundTasks, send_email: bool = True):
    with Session(engine) as session:
        run = Run(status="pending")
        session.add(run)
        session.commit()
        session.refresh(run)

    background_tasks.add_task(execute_run, run.id, send_email)
    return run
