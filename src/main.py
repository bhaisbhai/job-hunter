"""Entry point: scrape configured job sites, evaluate every listing with
the LLM against the user's criteria, and email a digest of the top matches.

Run with:  python -m src.main
"""

from __future__ import annotations

import logging

import anthropic

from src.emailer import send_digest
from src.evaluator import evaluate_all
from src.scraper import scrape_all
from src.settings import load_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    settings = load_settings()

    logger.info("Scraping %d configured URL(s)...", len(settings.target_urls))
    listings = scrape_all(
        settings.target_urls,
        headless=settings.headless,
        max_jobs_per_site=settings.max_jobs_per_site,
        page_timeout_ms=settings.page_timeout_ms,
    )
    logger.info("Found %d candidate listing(s) to evaluate.", len(listings))

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    evaluations = evaluate_all(client, settings.llm_model, listings, settings.criteria)
    logger.info("Evaluated %d listing(s).", len(evaluations))

    top_matches = sorted(
        (e for e in evaluations if e.match_score >= settings.min_match_score),
        key=lambda e: e.match_score,
        reverse=True,
    )
    logger.info("%d listing(s) scored >= %d.", len(top_matches), settings.min_match_score)

    send_digest(top_matches, settings.email_config, settings.smtp_password)


if __name__ == "__main__":
    main()
