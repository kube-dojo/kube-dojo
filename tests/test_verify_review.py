from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from verify_review import verify_review


def _review(path: str, line: int, code: str) -> str:
    return f"""FINDING: test
FILE:LINE: {path}:{line}
CURRENT CODE:
  {code}
WHY: reason
FIX: fix
"""


def test_verify_review_marks_verified_when_quote_matches_claimed_line():
    results = verify_review(_review("a.py", 2, "beta = 2"), lambda _path: "alpha = 1\nbeta = 2\ngamma = 3\n")
    assert results[0]["status"] == "verified"


def test_verify_review_marks_line_mismatch_when_quote_exists_elsewhere():
    results = verify_review(_review("a.py", 1, "beta = 2"), lambda _path: "alpha = 1\nbeta = 2\ngamma = 3\n")
    assert results[0]["status"] == "line_mismatch"


def test_verify_review_marks_quote_missing_for_hallucinated_code():
    results = verify_review(_review("a.py", 2, "delta = 4"), lambda _path: "alpha = 1\nbeta = 2\ngamma = 3\n")
    assert results[0]["status"] == "quote_missing"


def test_verify_review_handles_mixed_outcomes():
    review = "\n".join(
        [
            _review("a.py", 2, "beta = 2").strip(),
            _review("a.py", 1, "gamma = 3").strip(),
            _review("a.py", 4, "delta = 4").strip(),
        ]
    )
    results = verify_review(review, lambda _path: "alpha = 1\nbeta = 2\ngamma = 3\n")
    assert [result["status"] for result in results] == ["verified", "line_mismatch", "quote_missing"]
