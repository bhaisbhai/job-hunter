# Job Hunter

Automated job scraper and evaluator. It crawls a configurable list of job
board URLs with Playwright, extracts candidate listing text, has Claude
score each listing against your criteria (seniority, industry, location),
and emails you an HTML digest of everything that scores 7/10 or higher.

## Project structure

```
job-hunter/
├── config.yaml         # EDIT THIS: target URLs, destination email, criteria
├── .env.example        # copy to .env and fill in secrets
├── requirements.txt
├── src/
│   ├── settings.py      # loads config.yaml + .env
│   ├── scraper.py        # Playwright scraping + text extraction
│   ├── evaluator.py       # Claude structured-output evaluation
│   ├── emailer.py          # HTML digest + smtplib sending
│   └── main.py              # orchestrates the whole run
└── tests/                    # offline unit tests (no network/API calls)
```

## 1. Install

```bash
cd job-hunter
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 2. Configure

**`config.yaml`** — edit this directly. It's the single place to:

- Add/remove the URLs being crawled (`target_urls`)
- Set your destination email (`email.destination_email`)
- Set the sender account's SMTP host/port/address (`email.*`)
- Adjust match criteria and the score threshold (`criteria.*`)
- Choose the Claude model (`llm.model`)

**`.env`** — copy `.env.example` to `.env` and fill in the two secrets:

```bash
cp .env.example .env
```

```
SMTP_PASSWORD=your-smtp-app-password
ANTHROPIC_API_KEY=sk-ant-...
```

Secrets are kept out of `config.yaml` on purpose — that file is meant to be
freely readable/editable, and `.env` is git-ignored so a real key or
password never ends up in version control.

If you use Gmail as the sender, `smtp_host`/`smtp_port` in `config.yaml`
are already set for it; you'll need a Google **App Password** (not your
normal login password) for `SMTP_PASSWORD`.

## 3. Run it

```bash
python -m src.main
```

This scrapes every URL in `config.yaml`, evaluates each candidate listing
with Claude, and — if anything scores at or above `min_match_score` —
emails a digest to `destination_email`. If nothing qualifies, no email is
sent (this is logged, not an error).

## 4. Run the tests

The test suite mocks the Anthropic client, SMTP, and the Playwright page —
it needs no API key, no network access, and no browser install:

```bash
pytest
```

## Notes on scraping real job boards

Job board markup varies a lot and changes over time, and some sites (like
LinkedIn) actively try to block automated browsing. `scraper.py` uses a set
of common "job card" selectors (`article`, `li[class*=job]`, etc.) and
falls back to chunking the raw page text if none of them match, so a run
never silently returns zero listings for a page that actually loaded — but
for best results on a specific site you may want to add a selector to
`CARD_SELECTORS` in `src/scraper.py` that matches that site's markup.
Because the evaluator receives raw, possibly-messy text and is instructed
to score obviously-non-job text low, an imperfect extraction degrades to a
low `match_score` rather than a crash.
