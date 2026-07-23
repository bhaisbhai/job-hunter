# Scout

A generic crawl-and-evaluate engine with a live dashboard on top. Point it
at a list of URLs, describe what you're looking for in plain English, and
it crawls those pages with Playwright, has Gemini score every item it
finds against your instructions, emails you an HTML digest of everything
scoring at or above your threshold, and shows every run as a browsable
set of result cards in the dashboard.

The whole thing is defined by one config file — the same engine works
for job listings, apartment listings, product deals, event postings, or
anything else you can point a URL at and describe in a sentence.

## Project structure

```
scout/
├── config.yaml         # EDIT THIS: what to scout, where to look, where to send results
├── .env.example        # copy to .env and fill in secrets (local dev / CLI use)
├── requirements.txt     # shared scraping/evaluation/email deps
├── src/                  # core pipeline — used by both the CLI and the API
│   ├── settings.py
│   ├── scraper.py
│   ├── evaluator.py
│   ├── emailer.py
│   └── main.py            # CLI entry point: python -m src.main
├── tests/                  # offline unit tests for src/ (no network/API calls)
├── backend/                 # FastAPI web API wrapping src/, with run history
│   ├── app/
│   │   ├── main.py           # routes
│   │   ├── runner.py          # background scrape+evaluate+email job
│   │   ├── models.py           # Run / Item DB tables (SQLModel)
│   │   └── db.py                # SQLite by default; DATABASE_URL to use Postgres
│   └── requirements.txt
├── frontend/                # React + Tailwind dashboard
│   └── src/
├── Dockerfile               # builds the backend (Playwright + FastAPI) for deploy
└── render.yaml               # Render blueprint for the backend service
```

There are two independent ways to run this:

1. **CLI** (`python -m src.main`) — scrapes, evaluates, emails, exits. Good for a cron job.
2. **Web app** (`backend/` + `frontend/`) — same pipeline, triggered from a dashboard, with run history and a "Run Now" button. Both share the exact same `src/` code and `config.yaml`/`.env`.

---

## 1. Install

```bash
cd scout
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r backend/requirements.txt
playwright install chromium
```

## 2. Configure

**`config.yaml`** — edit this directly. It's the single place to:

- Define what this scout is looking for (`scout.name`, `scout.instructions` — free text, dropped straight into the LLM prompt)
- Set the score threshold for the digest (`scout.min_match_score`)
- Add/remove the URLs being crawled (`scout.target_urls`)
- Set your destination email (`email.destination_email`)
- Set the sender account's SMTP host/port/address (`email.*`)
- Choose the Gemini model (`llm.model`)

Repurposing Scout for something other than jobs means rewriting
`scout.instructions` and `scout.target_urls` — no code changes needed.

**`.env`** — copy `.env.example` to `.env` and fill in the two secrets:

```bash
cp .env.example .env
```

```
SMTP_PASSWORD=your-smtp-app-password
GEMINI_API_KEY=your-gemini-api-key
```

Secrets are kept out of `config.yaml` on purpose — that file is meant to be
freely readable/editable, and `.env` is git-ignored so a real key or
password never ends up in version control. In production (Render), these
same two values are set as dashboard env vars instead of a `.env` file —
see Deployment below.

If you use Gmail as the sender, `smtp_host`/`smtp_port` in `config.yaml`
are already set for it; you'll need a Google **App Password** (not your
normal login password) for `SMTP_PASSWORD`.

## 3. Run it — CLI

```bash
python -m src.main
```

Scrapes every URL in `config.yaml`, evaluates each candidate item with
Gemini against `scout.instructions`, and — if anything scores at or above
`min_match_score` — emails a digest to `destination_email`. If nothing
qualifies, no email is sent (this is logged, not an error).

## 4. Run it — web dashboard (local dev)

Two processes, run in separate terminals:

```bash
# Terminal 1 — backend API
source .venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```

```bash
# Terminal 2 — frontend
cd frontend
npm install
cp .env.example .env    # VITE_API_URL=http://localhost:8000
npm run dev
```

Open the printed `localhost:5173` URL. Click **Run Now** to trigger a
live scrape+evaluate cycle; the dashboard shows live progress ("12/51
evaluated") and renders each result as a card as soon as it's evaluated,
rather than waiting for the whole run to finish.

## 5. Run the tests

```bash
pytest
```

Mocks the Gemini client, SMTP, and the Playwright page — no API key,
network access, or browser install needed.

---

## Deployment

**Frontend → Vercel. Backend → Render.** They're split because Vercel's
serverless functions can't run Playwright (no persistent Chromium, and
execution time limits far shorter than a multi-site scrape+evaluate run)
— Render runs the backend as a normal long-lived container instead.

### Backend on Render

`render.yaml` at the repo root documents the service (Docker, health
check at `/api/health`) and can be deployed via Render's **Blueprint**
flow — but Blueprints can require a paid plan on some accounts. The
identical service can be created manually on the **Free** instance type
instead:

1. Push this repo to GitHub.
2. In Render: **New → Web Service** (not Blueprint), connect the repo.
3. Configure: **Branch** = your branch, **Root Directory** = blank (the
   `Dockerfile` is at the repo root), **Environment** = Docker,
   **Instance Type** = Free.
4. Set these environment variables on the service (Render dashboard →
   Environment):
   - `GEMINI_API_KEY`
   - `SMTP_PASSWORD`
   - `CORS_ORIGINS` — your Vercel frontend URL, e.g. `https://scout.vercel.app` (comma-separate multiple origins if needed)
5. Set the health check path to `/api/health`.
6. Deploy. Render builds the `Dockerfile`, which installs Chromium via
   `playwright install --with-deps chromium` — no extra setup needed for
   scraping to work.
7. Note the service's public URL (e.g. `https://scout-backend.onrender.com`) — the frontend needs it.

The Free instance type spins down after ~15 minutes of inactivity and
takes 30–60s to wake back up on the next request.

**Storage note:** by default the backend stores run history in a local
SQLite file. Render's free web service tier has an **ephemeral
filesystem** — that file resets whenever the service restarts, redeploys,
or spins down from inactivity. For run history that survives restarts,
either upgrade to a Render plan with a persistent **Disk** mounted at
`/app/backend/data`, or point `DATABASE_URL` (env var) at an external
Postgres instance (Render offers managed Postgres) — `db.py` already
supports both with no code changes; you'd just add `psycopg2-binary` to
`backend/requirements.txt`.

**Deploys interrupt active runs:** if Render's auto-deploy is on, every
push rebuilds and restarts the container — which kills whatever run is
currently in progress and, combined with the ephemeral filesystem above,
wipes its run history too. Avoid pushing/deploying while a real run is
active.

**Config note:** `config.yaml` is baked into the Docker image at deploy
time. Changing what's being scouted, the target URLs, or the email
threshold means editing `config.yaml` and redeploying — there's no
in-dashboard config editor in this build.

### Frontend on Vercel

1. In Vercel: **New Project**, import the same GitHub repo.
2. Set **Root Directory** to `frontend` (this is a monorepo — Vercel
   needs to know the frontend lives in a subfolder). Framework preset
   "Vite" should be auto-detected.
3. Set the environment variable:
   - `VITE_API_URL` — the Render backend URL from above, e.g. `https://scout-backend.onrender.com`
4. Deploy. Vercel builds with `npm run build` and serves `frontend/dist`.
5. Go back to Render and set `CORS_ORIGINS` to this Vercel URL (step 3 above), then redeploy the backend so it accepts requests from the live frontend.

### After both are live

Visit the Vercel URL, click **Run Now**. A full run against real sites can
take a while, especially on Gemini's free tier (which caps requests per
minute — Scout retries with backoff rather than giving up, so a run just
takes longer rather than failing outright). Consider lowering
`max_items_per_site` in `config.yaml` while testing to keep runs fast and
cheap, then raise it back up once you're happy with the results.

## Notes on scraping real sites

Site markup varies a lot and changes over time, and some sites (like
LinkedIn) actively try to block automated browsing. `src/scraper.py` uses
a set of common "card" selectors (`article`, `li[class*=card]`,
`div[class*=listing]`, etc.) and falls back to chunking the raw page text
if none of them match, so a run never silently returns zero items for a
page that actually loaded — but for best results on a specific site you
may want to add a selector to `CARD_SELECTORS` in `src/scraper.py` that
matches that site's markup. Because the evaluator receives raw,
possibly-messy text and is instructed to score obviously-irrelevant text
low, an imperfect extraction degrades to a low `match_score` rather than
a crash.
