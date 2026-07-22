"""Database engine setup.

Defaults to a local SQLite file so the app works with zero external
config. Set DATABASE_URL (e.g. a Postgres URL) to use a real database
instead — needed on hosts like Render's free tier, where the local
filesystem doesn't persist across restarts.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlmodel import SQLModel, create_engine

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    DB_PATH = Path(__file__).resolve().parent.parent / "data" / "job_hunter.db"
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
