# Time Machine

A version-history API for web pages. Give it any public URL and it keeps a
record of what that page actually said, so you can ask two questions no
normal bookmark can answer:

- What did this page say on a given date?
- What changed between two dates?

No logins, no credentials, no browser extensions. Every target is just a URL.

## How it works

A watcher polls each page in `pages.json` on an interval, keeps its visible
text, and saves a new snapshot only when the text really changed. Snapshots
are stored with timestamps in SQLite, and the API serves any date's version
plus a before-and-after diff.

- `GET /pages` — the watched pages
- `GET /pages/{id}/at?date=YYYY-MM-DD` — what a page said on a date
- `GET /pages/{id}/diff?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD` — what
  changed between two dates
- `GET /pages/{id}/snapshots` — the saved versions

A price-page mode compares only price-bearing lines, so rotating banners and
newsletter modules don't trigger false changes.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
.venv/bin/uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/pages. Swap the pages in `pages.json` for
pages you actually care about.

## Watcher

```bash
.venv/bin/python -m app.watcher --once   # one pass
.venv/bin/python -m app.watcher          # loop, respects check_every_minutes
```

On a real change, the watcher saves the new text snapshot and takes a
full-page screenshot with Playwright. Screenshots are best-effort: if the
screenshot fails, the snapshot still saves.

## Demo in 60 seconds (no waiting for a real change)

```bash
.venv/bin/python demo_seed.py
.venv/bin/uvicorn app.main:app --reload
```

Then:

- `GET /pages/saas-pricing/at?date=2026-11-01` → the old $20/mo price
- `GET /pages/saas-pricing/diff?from_date=2026-11-01&to_date=2026-11-02` →
  the $20 → $25 change plus the new Team plan

The seeded example is fake demo data, labeled as such wherever it appears.

## Real change caught in the wild

Watching Amazon Today's Deals, the history caught a genuine change within
minutes on November 2, 2026: "Holiday Shop" became "Holiday Gifts", plus a
new "25% off or more on home" deal line. Stripe's pricing page, watched over
the same period, showed no price change and no false alarms once
price-scoped comparison was on. Google's Privacy Policy and Terms of Service
stayed unchanged.

## Honest gaps

- **Automated screenshots depend on the machine.** The watcher takes a
  screenshot on every real change, but screenshot capture can fail in
  restricted environments (for example, behind a proxy that blocks the
  browser's network tunnel). Text snapshots always save; screenshots are
  best-effort.
- **Some sites refuse automated access.** Amazon, for example, blocks
  automated fetching outright, so its snapshots can come back as block pages
  instead of real content. Filtering block pages before saving is an open
  fix.
- **TinyFish Monitor wiring is outstanding.** This runs standalone; the
  connection into TinyFish Monitor itself is not yet done.
- **Deals pages churn constantly.** Most hourly differences on a deals page
  are rotation (deals cycling in and out), not durable changes.

## Layout

- `app/main.py` — FastAPI surface
- `app/watcher.py` — poll, hash, snapshot, screenshot
- `app/store.py` — SQLite snapshot store
- `app/diff.py` — before/after diffs
- `pages.json` — watchlist (URLs + check intervals)
- `demo_seed.py` — seeded demo data for the instant demo
