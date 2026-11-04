"""Watcher: poll pages, snapshot + screenshot whenever one changes.

Run once (test):  python -m app.watcher --once
Run forever:      python -m app.watcher   (respects each page's check_every_minutes)

The fetch goes through TinyFish Monitor in the real build; the local fetch
below is only so the scaffold runs end to end today. Screenshots are
best-effort: if the browser can't reach a page, the text snapshot is still
saved and the failure is logged instead of dropping the version.
"""

import hashlib
import json
import os
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

import httpx

from .store import latest_snapshot, save_snapshot

BASE = Path(__file__).resolve().parent.parent
PAGES_FILE = BASE / "pages.json"
SHOTS_DIR = BASE / "screenshots"


def _client() -> httpx.Client:
    # Explicit proxy (no trust_env): this sandbox's no_proxy list breaks
    # httpx's env parsing, and direct connections are blocked at the edge.
    proxy = (
        os.environ.get("https_proxy")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("http_proxy")
        or os.environ.get("HTTP_PROXY")
    )
    return httpx.Client(
        proxy=proxy,
        trust_env=False,
        # The egress proxy terminates TLS with its own CA; its bundle lives
        # in SSL_CERT_FILE, which trust_env=False would otherwise ignore.
        verify=os.environ.get("SSL_CERT_FILE", True),
        timeout=30,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0"},
    )


class _TextGrab(HTMLParser):
    """Visible text only: hashing raw HTML flags every markup tweak as a change."""

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


def extract_text(html: str) -> str:
    grab = _TextGrab()
    grab.feed(html)
    return re.sub(r"\n{2,}", "\n", "\n".join(grab.parts))


def fetch_text(url: str) -> str:
    """TODO: replace with the TinyFish Monitor read for the real build."""
    with _client() as client:
        resp = client.get(url)
    resp.raise_for_status()
    return extract_text(resp.text)


def take_screenshot(url: str, out_path: Path) -> str:
    """Full-page screenshot via Playwright. TODO: swap in Monitor screenshots.

    The browser needs the same egress proxy as the text fetch; without it
    the sandbox network refuses the tunnel outright.
    """
    from urllib.parse import urlparse

    from playwright.sync_api import sync_playwright

    proxy_url = (
        os.environ.get("https_proxy")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("http_proxy")
        or os.environ.get("HTTP_PROXY")
    )
    proxy = None
    if proxy_url:
        parts = urlparse(proxy_url)
        proxy = {"server": f"{parts.scheme}://{parts.hostname}:{parts.port}"}
        if parts.username:
            proxy["username"] = parts.username
        if parts.password:
            proxy["password"] = parts.password

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(proxy=proxy)
        try:
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.screenshot(path=str(out_path), full_page=True)
        finally:
            browser.close()
    return str(out_path)


def scoped_text(page: dict, text: str) -> str:
    """Text actually hashed for change detection.

    Default: the full extracted text. For a pricing page, only price-bearing
    lines ($ or %): Stripe's page rotates onboarding/newsletter modules
    ("Guide me", subscribe blocks) that full-text hashing flags as changes
    even though no price moved. The full text is still saved, so /at and
    /diff keep working; only the change trigger is scoped.
    """
    if page.get("hash_scope") == "price_lines":
        return "\n".join(l for l in text.splitlines() if "$" in l or "%" in l)
    return text


def check_page(page: dict) -> bool:
    """Fetch one page; save a snapshot only if the text actually changed."""
    text = fetch_text(page["url"])
    digest = hashlib.sha256(scoped_text(page, text).encode()).hexdigest()
    last = latest_snapshot(page["id"])
    # Re-scope the stored text rather than comparing to its stored hash:
    # pages that gain a hash_scope must not save one false snapshot first.
    last_digest = (
        hashlib.sha256(scoped_text(page, last["text"]).encode()).hexdigest()
        if last
        else None
    )
    if last and last_digest == digest:
        print(f"unchanged: {page['id']}")
        return False
    shot = None
    try:
        shot = take_screenshot(page["url"], SHOTS_DIR / page["id"] / f"{int(time.time())}.png")
    except Exception as exc:  # screenshot must never eat the version
        print(f"screenshot failed {page['id']} (snapshot still saved): {exc}")
    save_snapshot(page["id"], text, digest, shot)
    print(f"changed: {page['id']} -> snapshot saved" + (f" + {shot}" if shot else " (no screenshot)"))
    return True


def check_all(pages: list) -> None:
    for page in pages:
        try:
            check_page(page)
        except Exception as exc:  # keep watching the rest
            print(f"error {page['id']}: {exc}")


def main() -> None:
    once = "--once" in sys.argv
    pages = json.loads(PAGES_FILE.read_text())
    last_check: dict[str, float] = {}
    while True:
        now = time.time()
        due = [
            p
            for p in pages
            if now - last_check.get(p["id"], 0) >= p.get("check_every_minutes", 60) * 60
        ]
        for p in due:
            last_check[p["id"]] = now
        check_all(due)
        if once:
            break
        time.sleep(60)


if __name__ == "__main__":
    main()
