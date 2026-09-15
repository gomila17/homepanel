# homepanel

See `README.md` for what this project is, the stack, and local dev setup. This file is only about conventions for working in this repo.

## Versioning

- App version lives in `app/__init__.py` (`__version__`), semver, exposed via `/healthz` and the footer (`app_version` template context).
- Currently `0.1.0`. Bump it when a meaningful block of work lands (a new integration, a UI milestone), not on every commit.

## Commits

- Commit each closed logical block separately (one connector, one UI section, one cleanup) rather than batching everything at the end of a session.
- Commit message explains *why*, not just what changed.
- Never put real credentials or API keys in `.env.example` — it's tracked in git and this repo is public. Real values only go in `.env` (gitignored).

## Design reference

- `.local/Operations Console.dc.html` (gitignored, not tracked) is the visual mockup being matched for styling work. Read it directly when asked to match "the design".
- Match colors/spacing/typography closely, but don't invent fake data to fill a UI slot that has no real data source yet (e.g. a health aggregator that doesn't exist) — leave it static/placeholder and say so, rather than fabricating numbers that look live.

## Local dev server

- `.venv\Scripts\python -m uvicorn app.main:app --reload` (see README for full setup).
- `--reload` occasionally fails to pick up changes on Windows/WatchFiles (stale worker). If a change doesn't seem to apply after a save, fully stop and restart the process instead of trusting the auto-reload.
