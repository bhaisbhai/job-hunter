"""Unit tests for settings loading: GEMINI_API_KEY is required,
SMTP_PASSWORD is optional (email just gets skipped without it).
"""

from __future__ import annotations

import pytest
import yaml

from src.settings import load_settings

MINIMAL_CONFIG = {
    "target_urls": ["https://example.com/jobs"],
    "email": {
        "destination_email": "candidate@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "sender_email": "bot@example.com",
    },
    "llm": {"model": "gemini-2.5-flash"},
    "criteria": {
        "min_seniority": "Senior",
        "industry": "Sports",
        "location": "London",
        "min_match_score": 7,
    },
    "scraper": {"headless": True, "page_timeout_ms": 30000, "max_jobs_per_site": 25},
}


@pytest.fixture
def config_path(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(MINIMAL_CONFIG))
    return path


def test_load_settings_succeeds_without_smtp_password(config_path, monkeypatch):
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    settings = load_settings(config_path)

    assert settings.gemini_api_key == "fake-key"
    assert settings.smtp_password is None


def test_load_settings_raises_without_gemini_api_key(config_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("SMTP_PASSWORD", "hunter2")

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        load_settings(config_path)
