"""Unit tests for the LLM evaluator. The Anthropic client is mocked, so
these run offline with no API key and no network access.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from src.evaluator import JobEvaluation, evaluate_all, evaluate_listing
from src.scraper import JobListing

CRITERIA = {
    "min_seniority": "Senior/Director/Executive",
    "industry": "Sports",
    "location": "London",
}


def _fake_parse_response(parsed_output, stop_reason="end_turn"):
    response = MagicMock()
    response.stop_reason = stop_reason
    response.parsed_output = parsed_output
    return response


def test_evaluate_listing_returns_parsed_evaluation():
    expected = JobEvaluation(
        job_title="Head of Partnerships",
        company="Acme Sports",
        url="https://example.com/jobs/123",
        salary_range="£90,000 - £110,000",
        match_score=9,
        reasoning="Senior sports role based in London.",
    )
    client = MagicMock()
    client.messages.parse.return_value = _fake_parse_response(expected)

    result = evaluate_listing(
        client=client,
        model="claude-opus-4-8",
        raw_text="Head of Partnerships at Acme Sports, London, £90k-£110k",
        source_url="https://example.com/jobs",
        criteria=CRITERIA,
    )

    assert result == expected
    client.messages.parse.assert_called_once()
    _, kwargs = client.messages.parse.call_args
    assert kwargs["output_format"] is JobEvaluation
    assert kwargs["model"] == "claude-opus-4-8"


def test_evaluate_listing_returns_none_on_refusal():
    client = MagicMock()
    client.messages.parse.return_value = _fake_parse_response(None, stop_reason="refusal")

    result = evaluate_listing(
        client=client,
        model="claude-opus-4-8",
        raw_text="some listing text",
        source_url="https://example.com/jobs",
        criteria=CRITERIA,
    )

    assert result is None


def test_evaluate_listing_returns_none_on_api_error():
    client = MagicMock()
    client.messages.parse.side_effect = RuntimeError("network blip")

    result = evaluate_listing(
        client=client,
        model="claude-opus-4-8",
        raw_text="some listing text",
        source_url="https://example.com/jobs",
        criteria=CRITERIA,
    )

    assert result is None


def test_evaluate_all_skips_failed_evaluations():
    good = JobEvaluation(
        job_title="Director of Sport",
        company="Big League Co",
        url="https://example.com/jobs/1",
        salary_range=None,
        match_score=8,
        reasoning="Matches all criteria.",
    )
    client = MagicMock()
    client.messages.parse.side_effect = [
        _fake_parse_response(good),
        _fake_parse_response(None, stop_reason="refusal"),
    ]

    listings = [
        JobListing(source_url="https://example.com/a", raw_text="listing A"),
        JobListing(source_url="https://example.com/b", raw_text="listing B"),
    ]

    results = evaluate_all(client, "claude-opus-4-8", listings, CRITERIA)

    assert results == [good]
