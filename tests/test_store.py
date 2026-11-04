import pytest

from app import store


@pytest.fixture
 def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB", tmp_path / "time_machine.db")
    monkeypatch.setattr(store, "PAGES_FILE", tmp_path / "pages.json")
    store.PAGES_FILE.write_text("[]")
    return store


def save(isolated_store, page_id, ts, text):
    isolated_store.save_snapshot(page_id, text, f"hash-{text}", None, ts=ts)


def test_get_snapshot_at_returns_latest_snapshot_on_or_before_date(isolated_store):
    save(isolated_store, "pricing", "2026-01-01 09:00:00", "January")
    save(isolated_store, "pricing", "2026-01-02 12:00:00", "February")
    save(isolated_store, "pricing", "2026-01-03 08:00:00", "March")

    snapshot = isolated_store.get_snapshot_at("pricing", "2026-01-02")

    assert snapshot["text"] == "February"
    assert snapshot["ts"] == "2026-01-02 12:00:00"


def test_get_snapshot_at_returns_none_when_page_has_no_prior_snapshot(isolated_store):
    save(isolated_store, "pricing", "2026-01-02 12:00:00", "February")

    assert isolated_store.get_snapshot_at("pricing", "2026-01-01") is None


def test_get_snapshot_at_does_not_mix_pages(isolated_store):
    save(isolated_store, "pricing", "2026-01-01 09:00:00", "Pricing page")

    assert isolated_store.get_snapshot_at("privacy", "2026-01-02") is None


def test_latest_snapshot_and_history_are_newest_first(isolated_store):
    save(isolated_store, "pricing", "2026-01-01 09:00:00", "Old")
    save(isolated_store, "pricing", "2026-01-02 09:00:00", "New")

    assert isolated_store.latest_snapshot("pricing")["text"] == "New"
    assert [item["text"] for item in isolated_store.list_snapshots("pricing")] == [
        "New",
        "Old",
    ]
