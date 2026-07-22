"""LLM evaluator.

Sends each scraped listing's cleaned text to Claude and gets back a
strictly-typed JobEvaluation via structured outputs — no manual JSON
parsing or prompt-engineered format coaxing required.
"""

from __future__ import annotations

import logging
from typing import Optional

import anthropic
from pydantic import BaseModel, Field

from src.scraper import JobListing

logger = logging.getLogger(__name__)


class JobEvaluation(BaseModel):
    job_title: str
    company: str
    url: str
    salary_range: Optional[str] = None
    match_score: int = Field(ge=1, le=10)
    reasoning: str


def build_prompt(raw_text: str, source_url: str, criteria: dict) -> str:
    return f"""You are screening a single job listing for a candidate.

Candidate's criteria:
- Seniority level: {criteria['min_seniority']}
- Industry: {criteria['industry']}
- Location: {criteria['location']}

Job listing text (scraped from {source_url}):
---
{raw_text}
---

Extract the job details and evaluate how well this listing matches the
candidate's criteria above. If the listing text does not look like a real,
single job posting (e.g. it's navigation text, a cookie banner, or a list of
several unrelated jobs), still return your best-effort extraction but give it
a low match_score and explain why in reasoning. Use the listing's own URL if
one is visible in the text; otherwise use "{source_url}". salary_range should
be null if no salary is mentioned."""


def evaluate_listing(
    client: anthropic.Anthropic,
    model: str,
    raw_text: str,
    source_url: str,
    criteria: dict,
) -> Optional[JobEvaluation]:
    prompt = build_prompt(raw_text, source_url, criteria)
    try:
        response = client.messages.parse(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            output_format=JobEvaluation,
        )
    except anthropic.APIStatusError as exc:
        logger.warning("LLM evaluation failed for %s: %s", source_url, exc)
        return None
    except Exception as exc:
        logger.warning("Could not evaluate listing from %s: %s", source_url, exc)
        return None

    if getattr(response, "stop_reason", None) == "refusal" or response.parsed_output is None:
        logger.warning("LLM declined to evaluate listing from %s", source_url)
        return None

    return response.parsed_output


def evaluate_all(
    client: anthropic.Anthropic,
    model: str,
    listings: list[JobListing],
    criteria: dict,
) -> list[JobEvaluation]:
    results: list[JobEvaluation] = []
    for listing in listings:
        evaluation = evaluate_listing(client, model, listing.raw_text, listing.source_url, criteria)
        if evaluation is not None:
            results.append(evaluation)
    return results
