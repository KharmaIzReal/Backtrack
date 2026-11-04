"""Time Machine API: what did a page say on a date, and what changed?"""

from fastapi import FastAPI, HTTPException

from .diff import diff_texts
from .store import get_snapshot_at, list_pages, list_snapshots

app = FastAPI(title="Time Machine")


@app.get("/pages")
def pages():
    """Every watched page."""
    return list_pages()


@app.get("/pages/{page_id}/at")
def page_at(page_id: str, date: str):
    """What the page said and looked like on a given date (YYYY-MM-DD).

    Returns the latest snapshot at or before that date.
    """
    snap = get_snapshot_at(page_id, date)
    if snap is None:
        raise HTTPException(status_code=404, detail="No snapshot on or before that date")
    return snap


@app.get("/pages/{page_id}/diff")
def page_diff(page_id: str, from_date: str, to_date: str):
    """What changed between two dates (YYYY-MM-DD)."""
    old = get_snapshot_at(page_id, from_date)
    new = get_snapshot_at(page_id, to_date)
    if old is None or new is None:
        raise HTTPException(status_code=404, detail="Missing snapshot for one of the dates")
    return {
        "page_id": page_id,
        "from": old,
        "to": new,
        "text_diff": diff_texts(old["text"], new["text"]),
    }


@app.get("/pages/{page_id}/snapshots")
def snapshots(page_id: str):
    """Full version history for a page, newest first."""
    return list_snapshots(page_id)
