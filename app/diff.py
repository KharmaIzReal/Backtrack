"""Line diff between two snapshots, for the between-two-dates answer."""

import difflib


def diff_texts(old: str, new: str) -> list:
    return list(
        difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            fromfile="before",
            tofile="after",
            lineterm="",
        )
    )
