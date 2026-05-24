#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(cd "$ROOT/../.." && pwd)/.venv/bin/python"
fi
if [[ ! -x "$PYTHON" ]]; then
  echo "smoketest_review_verifier: missing .venv/bin/python" >&2
  exit 1
fi

REVIEW="$(cat <<'EOF'
FINDING: verified quote
FILE:LINE: fixture.py:2
CURRENT CODE:
  beta = 2
WHY: example
FIX: n/a

FINDING: hallucinated quote
FILE:LINE: fixture.py:4
CURRENT CODE:
  delta = 99
WHY: example
FIX: n/a
EOF
)"

OUTPUT="$(
  printf '%s\n' "$REVIEW" | "$PYTHON" -c "
import sys
from pathlib import Path

sys.path.insert(0, str(Path('scripts').resolve()))
from verify_review import verify_review

review = sys.stdin.read()
source = 'alpha = 1\nbeta = 2\ngamma = 3\n'
results = verify_review(review, lambda _path: source)
statuses = [row['status'] for row in results]
print(','.join(statuses))
if statuses != ['verified', 'quote_missing']:
    raise SystemExit(f'unexpected statuses: {statuses}')
"
)"

if [[ "$OUTPUT" != "verified,quote_missing" ]]; then
  echo "smoketest_review_verifier: expected verified,quote_missing got ${OUTPUT}" >&2
  exit 1
fi

echo "smoketest_review_verifier: ok (${OUTPUT})"
