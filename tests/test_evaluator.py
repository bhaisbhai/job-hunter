"""Unit tests for the LLM evaluator. The Gemini client is mocked, so
these run offline with no API key and no network access.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from google.genai import errors

from src.evaluator import JobEvaluation, evaluate_all, evaluate_listing
from src.scraper import JobListing

CRITERIA = {
    "min_seniority": "Senior/Director/Executive",
    "industry": "Sports",
    "location": "London",
}

MODEL = "gemini-2.5-flash"


def _fake_response(parsed):
    response = MagicMock()
    response.parsed = parsed
    return response


def _rate_limit_error(retry_delay: str = "14s") -> errors.ClientError:
    payload = {
        "error": {
            "code": 429,
            "message": "You exceeded your current quota...",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay},
            ],
        }
    }
    return errors.ClientError(429, payload)


def _bad_request_error() -> errors.ClientError:
    payload = {"error": {"code": 400, "message": "API key not valid.", "status": "INVALID_ARGUMENT"}}
    return errors.ClientError(400, payload)


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
    client.models.generate_content.return_value = _fake_response(expected)

    result = evaluate_listing(
        client=client,
        model=MODEL,
        raw_text="Head of Partnerships at Acme Sports, London, £90k-£110k",
        source_url="https://example.com/jobs",
        criteria=CRITERIA,
    )

    assert result == expected
    client.models.generate_content.assert_called_once()
    _, kwargs = client.models.generate_content.call_args
    assert kwargs["model"] == MODEL
    assert kwargs["config"].response_schema is JobEvaluation


def test_evaluate_listing_returns_none_when_unparsed():
    client = MagicMock()
    client.models.generate_content.return_value = _fake_response(None)

    result = evaluate_listing(
        client=client,
        model=MODEL,
        raw_text="some listing text",
        source_url="https://example.com/jobs",
        criteria=CRITERIA,
    )

    assert result is None


def test_evaluate_listing_returns_none_on_api_error():
    client = MagicMock()
    client.models.generate_content.side_effect = RuntimeError("network blip")

    result = evaluate_listing(
        client=client,
        model=MODEL,
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
    client.models.generate_content.side_effect = [
        _fake_response(good),
        _fake_response(None),
    ]

    listings = [
        JobListing(source_url="https://example.com/a", raw_text="listing A"),
        JobListing(source_url="https://example.com/b", raw_text="listing B"),
    ]

    results = evaluate_all(client, MODEL, listings, CRITERIA)

    assert results == [good]


def test_evaluate_listing_retries_after_rate_limit_then_succeeds():
    expected = JobEvaluation(
        job_title="Head of Partnerships",
        company="Acme Sports",
        url="https://example.com/jobs/123",
        salary_range=None,
        match_score=8,
        reasoning="Matches criteria.",
    )
    client = MagicMock()
    client.models.generate_content.side_effect = [_rate_limit_error("14s"), _fake_response(expected)]

    with patch("src.evaluator.time.sleep") as mock_sleep:
        result = evaluate_listing(
            client=client,
            model=MODEL,
            raw_text="some listing text",
            source_url="https://example.com/jobs",
            criteria=CRITERIA,
        )

    assert result == expected
    assert client.models.generate_content.call_count == 2
    mock_sleep.assert_called_once_with(14.0)


def test_evaluate_listing_gives_up_after_max_rate_limit_retries():
    client = MagicMock()
    client.models.generate_content.side_effect = _rate_limit_error("1s")

    with patch("src.evaluator.time.sleep"):
        result = evaluate_listing(
            client=client,
            model=MODEL,
            raw_text="some listing text",
            source_url="https://example.com/jobs",
            criteria=CRITERIA,
        )

    assert result is None
    assert client.models.generate_content.call_count == 5  # MAX_RATE_LIMIT_RETRIES


def test_evaluate_listing_does_not_retry_non_rate_limit_client_error():
    client = MagicMock()
    client.models.generate_content.side_effect = _bad_request_error()

    with patch("src.evaluator.time.sleep") as mock_sleep:
        result = evaluate_listing(
            client=client,
            model=MODEL,
            raw_text="some listing text",
            source_url="https://example.com/jobs",
            criteria=CRITERIA,
        )

    assert result is None
    assert client.models.generate_content.call_count == 1
    mock_sleep.assert_not_called()
