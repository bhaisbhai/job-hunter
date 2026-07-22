"""Unit tests for the scraper's text-extraction logic. These test the
pure extraction functions against a mocked Playwright Page — no browser
is launched, so these run offline and fast.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from src.scraper import MIN_BLOCK_CHARS, _extract_cards, _fallback_page_text


def _mock_element(text: str):
    el = MagicMock()
    el.inner_text.return_value = text
    return el


def test_extract_cards_finds_matching_selector():
    long_enough = "x" * MIN_BLOCK_CHARS

    page = MagicMock()

    def query_selector_all(selector):
        if selector == "article":
            return [_mock_element(f"Job A {long_enough}"), _mock_element(f"Job B {long_enough}")]
        return []

    page.query_selector_all.side_effect = query_selector_all

    blocks = _extract_cards(page)

    assert len(blocks) == 2
    assert any("Job A" in b for b in blocks)
    assert any("Job B" in b for b in blocks)


def test_extract_cards_returns_empty_when_no_selector_matches():
    page = MagicMock()
    page.query_selector_all.return_value = []

    assert _extract_cards(page) == []


def test_extract_cards_dedupes_and_filters_short_blocks():
    long_enough = "y" * MIN_BLOCK_CHARS
    page = MagicMock()

    def query_selector_all(selector):
        if selector == "article":
            return [
                _mock_element(f"Job A {long_enough}"),
                _mock_element(f"Job A {long_enough}"),  # duplicate
                _mock_element("too short"),  # below MIN_BLOCK_CHARS
            ]
        return []

    page.query_selector_all.side_effect = query_selector_all

    blocks = _extract_cards(page)

    # duplicate collapsed away, short block dropped, so no distinct pair remains
    assert blocks == []


def test_fallback_page_text_chunks_body_text():
    page = MagicMock()
    page.inner_text.return_value = "word " * 2000  # long body text

    chunks = _fallback_page_text(page)

    assert len(chunks) >= 1
    assert all(len(c) >= MIN_BLOCK_CHARS for c in chunks)


def test_fallback_page_text_handles_empty_body():
    page = MagicMock()
    page.inner_text.return_value = "   "

    assert _fallback_page_text(page) == []
