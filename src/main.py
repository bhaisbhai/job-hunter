"""Entry point: scrape the configured scout's target URLs, evaluate every
item found against its instructions, and email a digest of the top matches.

Run with:  python -m src.main
"""

from __future__ import annotations

import logging

from google import genai

from src.emailer import send_digest
from src.evaluator import evaluate_all
from src.scraper import scrape_all
from src.settings import load_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    settings = load_settings()

    logger.info("[%s] Scraping %d configured URL(s)...", settings.scout_name, len(settings.target_urls))
    listings = scrape_all(
        settings.target_urls,
        headless=settings.headless,
        max_items_per_site=settings.max_items_per_site,
        page_timeout_ms=settings.page_timeout_ms,
    )
    logger.info("Found %d candidate item(s) to evaluate.", len(listings))

    client = genai.Client(api_key=settings.gemini_api_key)
    evaluations = evaluate_all(client, settings.llm_model, listings, settings.scout_instructions)
    logger.info("Evaluated %d item(s).", len(evaluations))

    top_matches = sorted(
        (e for e in evaluations if e.match_score >= settings.min_match_score),
        key=lambda e: e.match_score,
        reverse=True,
    )
    logger.info("%d item(s) scored >= %d.", len(top_matches), settings.min_match_score)

    send_digest(top_matches, settings.email_config, settings.smtp_password, settings.scout_name)


if __name__ == "__main__":
    main()
