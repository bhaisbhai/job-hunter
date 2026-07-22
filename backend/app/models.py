"""Persisted run history: one Run per scrape+evaluate cycle, with its
matched JobMatch rows."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Run(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    started_at: datetime = Field(default_factory=_now)
    finished_at: Optional[datetime] = None
    # pending -> scraping -> evaluating -> completed | failed
    status: str = "pending"
    listings_scraped: int = 0
    evaluated_count: int = 0
    matched_count: int = 0
    email_sent: bool = False
    error_message: Optional[str] = None


class JobMatch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    job_title: str
    company: str
    url: str
    salary_range: Optional[str] = None
    match_score: int
    reasoning: str
    source_url: str
