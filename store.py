"""Snapshot store: SQLite, one row per page version."""

import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "time_machine.db"
PAGES_FILE = BASE / "pages.json"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS snapshots (
            page_id TEXT, ts TEXT DEFAULT (datetime('now')),
            content_hash TEXT, text TEXT, screenshot_path TEXT
        )"""
    )
    return conn


def list_pages() -> list:
    return json.loads(PAGES_FILE.read_text())


def save_snapshot(page_id: str, text: str, content_hash: str, screenshot_path: str,
                   ts: str | None = None) -> None:
    with _conn() as conn:
        if ts is None:
            conn.execute(
                "INSERT INTO snapshots (page_id, content_hash, text, screenshot_path)"
                " VALUES (?, ?, ?, ?)",
                (page_id, content_hash, text, screenshot_path),
            )
        else:
            conn.execute(
                "INSERT INTO snapshots (page_id, ts, content_hash, text, screenshot_path)"
                " VALUES (?, ?, ?, ?, ?)",
                (page_id, ts, content_hash, text, screenshot_path),
            )


def latest_snapshot(page_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM snapshots WHERE page_id = ? ORDER BY ts DESC LIMIT 1",
            (page_id,),
        ).fetchone()
    return dict(row) if row else None


def get_snapshot_at(page_id: str, date: str) -> dict | None:
    """Latest snapshot at or before the end of the given date (YYYY-MM-DD)."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM snapshots WHERE page_id = ? AND date(ts) <= ?"
            " ORDER BY ts DESC LIMIT 1",
            (page_id, date),
        ).fetchone()
    return dict(row) if row else None


def list_snapshots(page_id: str) -> list:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM snapshots WHERE page_id = ? ORDER BY ts DESC",
            (page_id,),
        ).fetchall()
    return [dict(r) for r in rows]
