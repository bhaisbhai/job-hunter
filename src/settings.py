"""Loads all runtime configuration.

Non-secret settings (target URLs, criteria, SMTP host, etc.) come from
config.yaml, which is meant to be edited directly by the end user.
Secrets (SMTP password, Gemini API key) come from environment
variables, loaded from a local .env file — see .env.example.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Settings:
    target_urls: list[str]

    destination_email: str
    smtp_host: str
    smtp_port: int
    sender_email: str
    smtp_password: str

    llm_model: str
    gemini_api_key: str

    min_seniority: str
    industry: str
    location: str
    min_match_score: int

    headless: bool
    page_timeout_ms: int
    max_jobs_per_site: int

    @property
    def email_config(self) -> dict:
        return {
            "destination_email": self.destination_email,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "sender_email": self.sender_email,
        }

    @property
    def criteria(self) -> dict:
        return {
            "min_seniority": self.min_seniority,
            "industry": self.industry,
            "location": self.location,
        }


def load_settings(config_path: Path = CONFIG_PATH) -> Settings:
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)

    smtp_password = os.environ.get("SMTP_PASSWORD")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")

    missing = [
        name
        for name, val in [
            ("SMTP_PASSWORD", smtp_password),
            ("GEMINI_API_KEY", gemini_api_key),
        ]
        if not val
    ]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )

    return Settings(
        target_urls=list(raw["target_urls"]),
        destination_email=raw["email"]["destination_email"],
        smtp_host=raw["email"]["smtp_host"],
        smtp_port=int(raw["email"]["smtp_port"]),
        sender_email=raw["email"]["sender_email"],
        smtp_password=smtp_password,
        llm_model=raw["llm"]["model"],
        gemini_api_key=gemini_api_key,
        min_seniority=raw["criteria"]["min_seniority"],
        industry=raw["criteria"]["industry"],
        location=raw["criteria"]["location"],
        min_match_score=int(raw["criteria"]["min_match_score"]),
        headless=bool(raw["scraper"]["headless"]),
        page_timeout_ms=int(raw["scraper"]["page_timeout_ms"]),
        max_jobs_per_site=int(raw["scraper"]["max_jobs_per_site"]),
    )
