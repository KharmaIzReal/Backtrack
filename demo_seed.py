"""Seed a before/after demo: two versions of the pricing page on two dates.

Run:  python demo_seed.py
Then:  GET /pages/saas-pricing/at?date=2026-11-01   -> old price
       GET /pages/saas-pricing/diff?from_date=2026-11-01&to_date=2026-11-02
"""

import hashlib

from app.store import save_snapshot

OLD = """Acme Cloud — Pricing
Starter: $20/mo — 10 projects
Pro: $50/mo — unlimited projects
"""

NEW = """Acme Cloud — Pricing
Starter: $25/mo — 10 projects
Pro: $50/mo — unlimited projects
New: Team plan $99/mo
"""

save_snapshot(
    "saas-pricing", OLD, hashlib.sha256(OLD.encode()).hexdigest(),
    "screenshots/saas-pricing/before.png", ts="2026-11-01 09:00:00",
)
save_snapshot(
    "saas-pricing", NEW, hashlib.sha256(NEW.encode()).hexdigest(),
    "screenshots/saas-pricing/after.png", ts="2026-11-02 09:00:00",
)
print("seeded: saas-pricing has a before (2026-11-01) and after (2026-11-02)")
