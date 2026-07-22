"""Playwright-based scraper.

Iterates the configured target URLs, waits for dynamic (JS-rendered)
content to load, and extracts candidate job-listing text blocks. Real
job boards vary widely in markup, so this uses a small set of common
"job card" selectors first, and falls back to chunking the page's
visible text if none of them match — see README for tuning notes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

logger = logging.getLogger(__name__)

# Tried in order against each listing page to find repeated job-card
# containers. Not site-specific — covers common patterns across job boards.
CARD_SELECTORS = [
    "article",
    "li[class*='job']",
    "div[class*='job-card']",
    "div[class*='job-listing']",
    "div[class*='vacancy']",
    "a[href*='job']",
]

MIN_BLOCK_CHARS = 40
MAX_BLOCK_CHARS = 4000

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class JobListing:
    source_url: str
    raw_text: str


def _extract_cards(page: Page) -> list[str]:
    for selector in CARD_SELECTORS:
        try:
            elements = page.query_selector_all(selector)
        except Exception:
            continue

        texts: list[str] = []
        for el in elements:
            try:
                text = el.inner_text().strip()
            except Exception:
                continue
            if MIN_BLOCK_CHARS <= len(text) <= MAX_BLOCK_CHARS:
                texts.append(text)

        deduped = list(dict.fromkeys(texts))  # preserve order, drop dupes
        if len(deduped) >= 2:
            return deduped
    return []


def _fallback_page_text(page: Page) -> list[str]:
    """Chunk the raw visible page text so a page with no matched selectors
    still produces evaluable blocks instead of being silently skipped."""
    try:
        body_text = page.inner_text("body").strip()
    except Exception:
        return []
    if not body_text:
        return []

    chunks = []
    for i in range(0, len(body_text), MAX_BLOCK_CHARS):
        chunk = body_text[i : i + MAX_BLOCK_CHARS].strip()
        if len(chunk) >= MIN_BLOCK_CHARS:
            chunks.append(chunk)
    return chunks


def scrape_url(page: Page, url: str, max_jobs: int, timeout_ms: int) -> list[JobListing]:
    logger.info("Scraping %s", url)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(2000)  # let JS-rendered content settle
    except PlaywrightTimeoutError:
        logger.warning("Timed out loading %s", url)
        return []
    except Exception as exc:
        logger.warning("Failed to load %s: %s", url, exc)
        return []

    blocks = _extract_cards(page)
    if not blocks:
        blocks = _fallback_page_text(page)

    return [JobListing(source_url=url, raw_text=block) for block in blocks[:max_jobs]]


def scrape_all(
    urls: list[str],
    headless: bool,
    max_jobs_per_site: int,
    page_timeout_ms: int,
) -> list[JobListing]:
    listings: list[JobListing] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        try:
            for url in urls:
                listings.extend(scrape_url(page, url, max_jobs_per_site, page_timeout_ms))
        finally:
            browser.close()
    return listings
