"""Executes one full scrape -> evaluate -> (optionally) email cycle as a
background job, updating the Run row's status as it progresses so the
frontend can poll and show live stage information.
"""

from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone

from google import genai
from sqlmodel import Session

from src.emailer import send_digest
from src.evaluator import JobEvaluation, evaluate_listing
from src.scraper import scrape_all
from src.settings import load_settings

from .db import engine
from .models import JobMatch, Run

logger = logging.getLogger(__name__)


def _set_status(run_id: str, **fields) -> None:
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if run is None:
            return
        for key, value in fields.items():
            setattr(run, key, value)
        session.add(run)
        session.commit()


def execute_run(run_id: str, send_email: bool) -> None:
    _set_status(run_id, status="scraping")

    try:
        settings = load_settings()

        listings = scrape_all(
            settings.target_urls,
            headless=settings.headless,
            max_jobs_per_site=settings.max_jobs_per_site,
            page_timeout_ms=settings.page_timeout_ms,
        )
        _set_status(run_id, status="evaluating", listings_scraped=len(listings))

        client = genai.Client(api_key=settings.gemini_api_key)
        matches: list[JobMatch] = []
        evaluation_failures = 0
        for listing in listings:
            evaluation = evaluate_listing(
                client, settings.llm_model, listing.raw_text, listing.source_url, settings.criteria
            )
            if evaluation is None:
                evaluation_failures += 1
            else:
                match = JobMatch(
                    run_id=run_id,
                    job_title=evaluation.job_title,
                    company=evaluation.company,
                    url=evaluation.url,
                    salary_range=evaluation.salary_range,
                    match_score=evaluation.match_score,
                    reasoning=evaluation.reasoning,
                    source_url=listing.source_url,
                )
                matches.append(match)
                with Session(engine) as session:
                    session.add(match)
                    session.commit()

            # Persist after every listing (not just at the end) so the
            # frontend's poll shows live "X/Y evaluated" progress, and so
            # results survive even if something fails partway through.
            _set_status(
                run_id,
                evaluated_count=len(matches),
                evaluation_failures=evaluation_failures,
            )

        top_matches = sorted(
            (m for m in matches if m.match_score >= settings.min_match_score),
            key=lambda m: m.match_score,
            reverse=True,
        )

        email_sent = False
        if send_email and top_matches:
            digest_jobs = [
                JobEvaluation(
                    job_title=m.job_title,
                    company=m.company,
                    url=m.url,
                    salary_range=m.salary_range,
                    match_score=m.match_score,
                    reasoning=m.reasoning,
                )
                for m in top_matches
            ]
            try:
                email_sent = send_digest(digest_jobs, settings.email_config, settings.smtp_password)
            except Exception:
                # A broken email step shouldn't discard results the scrape/evaluate
                # stages already produced — log it and let the run complete.
                logger.exception("Failed to send digest email for run %s", run_id)

        # Matches were already persisted incrementally as they were evaluated —
        # only the Run's terminal state is left to record.
        _set_status(
            run_id,
            status="completed",
            finished_at=datetime.now(timezone.utc),
            matched_count=len(top_matches),
            email_sent=email_sent,
        )

    except Exception:
        logger.exception("Run %s failed", run_id)
        _set_status(
            run_id,
            status="failed",
            finished_at=datetime.now(timezone.utc),
            error_message=traceback.format_exc()[-2000:],
        )
