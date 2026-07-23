"""Unit tests for the email digest builder and sender. smtplib is mocked,
so these run offline and never actually send an email.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.emailer import build_digest_html, send_digest
from src.evaluator import ScoutedItem

EMAIL_CONFIG = {
    "destination_email": "candidate@example.com",
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "sender_email": "bot@example.com",
}

SCOUT_NAME = "Sports Executive Jobs - London"  # plain ASCII, so it survives raw Subject header encoding unmangled

ITEM = ScoutedItem(
    title="Chief Commercial Officer",
    subtitle="Elite Sports Group",
    url="https://example.com/jobs/ccо",
    price="£150,000+",
    match_score=9,
    reasoning="Executive-level sports role in London.",
)


def test_build_digest_html_includes_item_details():
    html = build_digest_html([ITEM], SCOUT_NAME)

    assert "Chief Commercial Officer" in html
    assert "Elite Sports Group" in html
    assert "9/10" in html
    assert "£150,000+" in html
    assert "https://example.com/jobs/cc" in html  # href present
    assert SCOUT_NAME in html


def test_build_digest_html_escapes_content():
    dangerous = ITEM.model_copy(update={"subtitle": "<script>alert(1)</script>"})
    html = build_digest_html([dangerous], SCOUT_NAME)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_send_digest_skips_when_no_items():
    with patch("src.emailer.smtplib.SMTP") as smtp_cls:
        sent = send_digest([], EMAIL_CONFIG, sender_password="hunter2", scout_name=SCOUT_NAME)
        assert sent is False
        smtp_cls.assert_not_called()


def test_send_digest_skips_when_no_password_configured():
    with patch("src.emailer.smtplib.SMTP") as smtp_cls:
        sent = send_digest([ITEM], EMAIL_CONFIG, sender_password=None, scout_name=SCOUT_NAME)
        assert sent is False
        smtp_cls.assert_not_called()


def test_send_digest_sends_via_smtp():
    smtp_instance = MagicMock()
    with patch("src.emailer.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__.return_value = smtp_instance

        sent = send_digest([ITEM], EMAIL_CONFIG, sender_password="hunter2", scout_name=SCOUT_NAME)

        assert sent is True
        smtp_cls.assert_called_once_with(
            EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"]
        )
        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with(
            EMAIL_CONFIG["sender_email"], "hunter2"
        )
        smtp_instance.sendmail.assert_called_once()
        args, _ = smtp_instance.sendmail.call_args
        assert args[0] == EMAIL_CONFIG["sender_email"]
        assert args[1] == [EMAIL_CONFIG["destination_email"]]
        # The HTML body is base64-encoded by MIMEText, so check the
        # unencoded envelope instead of the raw message string.
        assert f"{SCOUT_NAME}: 1 new match(es)" in args[2]
