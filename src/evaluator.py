"""LLM evaluator.

Sends each scraped item's cleaned text to Gemini and gets back a
strictly-typed ScoutedItem via structured output — no manual JSON
parsing or prompt-engineered format coaxing required. What counts as
a match is entirely driven by the scout's free-text `instructions`,
so this same code evaluates jobs, apartments, deals, or anything else
a scout is configured to look for.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from src.scraper import ScrapedListing

logger = logging.getLogger(__name__)

MAX_RATE_LIMIT_RETRIES = 5
DEFAULT_RETRY_DELAY_SECONDS = 15.0
MAX_RETRY_DELAY_SECONDS = 90.0


class ScoutedItem(BaseModel):
    title: str
    subtitle: str
    url: str
    price: Optional[str] = None
    match_score: int = Field(ge=1, le=10)
    reasoning: str


def build_prompt(raw_text: str, source_url: str, instructions: str) -> str:
    return f"""You are screening a single item scraped from a web page for a scout.

What this scout is looking for:
{instructions}

Scraped text (from {source_url}):
---
{raw_text}
---

Extract the item's details and evaluate how well it matches what the scout
is looking for. If the text does not look like a real, single item (e.g.
it's navigation text, a cookie banner, or a list of several unrelated
items), still return your best-effort extraction but give it a low
match_score and explain why in reasoning. Use the item's own URL if one is
visible in the text; otherwise use "{source_url}". title is the item's name
or headline; subtitle is its secondary identifier (company, seller,
landlord, publisher — whatever fits). price should be null if no
price/salary/cost is mentioned."""


def _retry_delay_seconds(exc: errors.ClientError) -> float:
    """Reads Google's own suggested backoff out of a 429 response instead of
    guessing — self-adapts to whatever quota actually applies."""
    try:
        details = exc.details.get("error", {}).get("details", [])
        for detail in details:
            if detail.get("@type", "").endswith("RetryInfo"):
                raw_delay = detail.get("retryDelay", "")
                if raw_delay.endswith("s"):
                    return min(float(raw_delay[:-1]), MAX_RETRY_DELAY_SECONDS)
    except (AttributeError, TypeError, ValueError):
        pass
    return DEFAULT_RETRY_DELAY_SECONDS


def evaluate_listing(
    client: genai.Client,
    model: str,
    raw_text: str,
    source_url: str,
    instructions: str,
) -> Optional[ScoutedItem]:
    prompt = build_prompt(raw_text, source_url, instructions)

    for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ScoutedItem,
                ),
            )
        except errors.ClientError as exc:
            if exc.code == 429 and attempt < MAX_RATE_LIMIT_RETRIES:
                delay = _retry_delay_seconds(exc)
                logger.info(
                    "Rate limited evaluating %s (attempt %d/%d) — retrying in %.0fs",
                    source_url,
                    attempt,
                    MAX_RATE_LIMIT_RETRIES,
                    delay,
                )
                time.sleep(delay)
                continue
            logger.warning("LLM evaluation failed for %s: %s", source_url, exc)
            return None
        except Exception as exc:
            logger.warning("Could not evaluate listing from %s: %s", source_url, exc)
            return None

        if response.parsed is None:
            logger.warning("LLM declined to evaluate listing from %s", source_url)
            return None

        return response.parsed

    return None


def evaluate_all(
    client: genai.Client,
    model: str,
    listings: list[ScrapedListing],
    instructions: str,
) -> list[ScoutedItem]:
    results: list[ScoutedItem] = []
    for listing in listings:
        evaluation = evaluate_listing(client, model, listing.raw_text, listing.source_url, instructions)
        if evaluation is not None:
            results.append(evaluation)
    return results
