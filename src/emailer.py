"""Formats the top-matching scouted items into a clean HTML digest and
sends it over SMTP using only Python's built-in smtplib/email modules.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import Optional

from src.evaluator import ScoutedItem

logger = logging.getLogger(__name__)


def _item_row_html(item: ScoutedItem) -> str:
    price = escape(item.price) if item.price else "Not specified"
    return f"""
    <tr>
      <td style="padding:12px;border-bottom:1px solid #e5e5e5;">
        <div style="font-size:16px;font-weight:600;color:#111;">
          <a href="{escape(item.url)}" style="color:#0b5fff;text-decoration:none;">{escape(item.title)}</a>
        </div>
        <div style="font-size:14px;color:#555;margin-top:2px;">{escape(item.subtitle)}</div>
        <div style="font-size:13px;color:#777;margin-top:6px;">{escape(item.reasoning)}</div>
      </td>
      <td style="padding:12px;border-bottom:1px solid #e5e5e5;text-align:center;vertical-align:top;white-space:nowrap;">
        <span style="display:inline-block;background:#0b5fff;color:#fff;border-radius:12px;padding:2px 10px;font-size:13px;font-weight:600;">
          {item.match_score}/10
        </span>
      </td>
      <td style="padding:12px;border-bottom:1px solid #e5e5e5;text-align:right;vertical-align:top;font-size:13px;color:#555;white-space:nowrap;">
        {price}
      </td>
    </tr>"""


def build_digest_html(items: list[ScoutedItem], scout_name: str) -> str:
    rows = "\n".join(_item_row_html(i) for i in items)
    return f"""\
<html>
  <body style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#f4f4f4;padding:24px;">
    <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;">
      <div style="background:#111;padding:20px 24px;">
        <h1 style="color:#fff;font-size:20px;margin:0;">{escape(scout_name)}</h1>
        <p style="color:#aaa;font-size:13px;margin:4px 0 0;">{len(items)} top match(es) found</p>
      </div>
      <table style="width:100%;border-collapse:collapse;">
        {rows}
      </table>
      <div style="padding:16px 24px;font-size:12px;color:#999;">
        Generated automatically by Scout.
      </div>
    </div>
  </body>
</html>"""


def send_digest(
    items: list[ScoutedItem],
    email_config: dict,
    sender_password: Optional[str],
    scout_name: str,
) -> bool:
    """Returns True if the digest was actually sent, False if it was skipped
    (no matches, or no SMTP password configured)."""
    if not items:
        logger.info("No items scored high enough this run; skipping email.")
        return False

    if not sender_password:
        logger.info("SMTP_PASSWORD not configured; skipping email digest.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{scout_name}: {len(items)} new match(es)"
    msg["From"] = email_config["sender_email"]
    msg["To"] = email_config["destination_email"]
    msg.attach(MIMEText(build_digest_html(items, scout_name), "html"))

    with smtplib.SMTP(email_config["smtp_host"], email_config["smtp_port"]) as server:
        server.starttls()
        server.login(email_config["sender_email"], sender_password)
        server.sendmail(
            email_config["sender_email"],
            [email_config["destination_email"]],
            msg.as_string(),
        )

    logger.info(
        "Sent digest with %d item(s) to %s", len(items), email_config["destination_email"]
    )
    return True
