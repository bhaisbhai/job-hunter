"""Formats the top-matching jobs into a clean HTML digest and sends it
over SMTP using only Python's built-in smtplib/email modules.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from src.evaluator import JobEvaluation

logger = logging.getLogger(__name__)


def _job_row_html(job: JobEvaluation) -> str:
    salary = escape(job.salary_range) if job.salary_range else "Not specified"
    return f"""
    <tr>
      <td style="padding:12px;border-bottom:1px solid #e5e5e5;">
        <div style="font-size:16px;font-weight:600;color:#111;">
          <a href="{escape(job.url)}" style="color:#0b5fff;text-decoration:none;">{escape(job.job_title)}</a>
        </div>
        <div style="font-size:14px;color:#555;margin-top:2px;">{escape(job.company)}</div>
        <div style="font-size:13px;color:#777;margin-top:6px;">{escape(job.reasoning)}</div>
      </td>
      <td style="padding:12px;border-bottom:1px solid #e5e5e5;text-align:center;vertical-align:top;white-space:nowrap;">
        <span style="display:inline-block;background:#0b5fff;color:#fff;border-radius:12px;padding:2px 10px;font-size:13px;font-weight:600;">
          {job.match_score}/10
        </span>
      </td>
      <td style="padding:12px;border-bottom:1px solid #e5e5e5;text-align:right;vertical-align:top;font-size:13px;color:#555;white-space:nowrap;">
        {salary}
      </td>
    </tr>"""


def build_digest_html(jobs: list[JobEvaluation]) -> str:
    rows = "\n".join(_job_row_html(j) for j in jobs)
    return f"""\
<html>
  <body style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#f4f4f4;padding:24px;">
    <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;">
      <div style="background:#111;padding:20px 24px;">
        <h1 style="color:#fff;font-size:20px;margin:0;">Your Job Digest</h1>
        <p style="color:#aaa;font-size:13px;margin:4px 0 0;">{len(jobs)} role(s) scored 7 or higher</p>
      </div>
      <table style="width:100%;border-collapse:collapse;">
        {rows}
      </table>
      <div style="padding:16px 24px;font-size:12px;color:#999;">
        Generated automatically by Job Hunter.
      </div>
    </div>
  </body>
</html>"""


def send_digest(jobs: list[JobEvaluation], email_config: dict, sender_password: str) -> None:
    if not jobs:
        logger.info("No jobs scored high enough this run; skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Job Digest: {len(jobs)} new match(es)"
    msg["From"] = email_config["sender_email"]
    msg["To"] = email_config["destination_email"]
    msg.attach(MIMEText(build_digest_html(jobs), "html"))

    with smtplib.SMTP(email_config["smtp_host"], email_config["smtp_port"]) as server:
        server.starttls()
        server.login(email_config["sender_email"], sender_password)
        server.sendmail(
            email_config["sender_email"],
            [email_config["destination_email"]],
            msg.as_string(),
        )

    logger.info(
        "Sent digest with %d job(s) to %s", len(jobs), email_config["destination_email"]
    )
