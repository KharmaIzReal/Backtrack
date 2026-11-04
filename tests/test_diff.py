import pytest

from app.diff import diff_texts


def test_diff_reports_added_and_removed_lines():
    old = "Starter: $20/mo\nPro: $50/mo"
    new = "Starter: $25/mo\nPro: $50/mo\nTeam: $99/mo"

    assert diff_texts(old, new) == [
        "--- before",
        "+++ after",
        "@@ -1,2 +1,3 @@",
        "-Starter: $20/mo",
        "+Starter: $25/mo",
        " Pro: $50/mo",
        "+Team: $99/mo",
    ]


def test_identical_text_has_no_diff():
    assert diff_texts("same\ntext", "same\ntext") == []
