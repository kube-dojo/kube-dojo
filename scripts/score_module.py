#!/usr/bin/env python3
"""Score a module against the KubeDojo quality rubric.

Canonical rubric: docs/quality-rubric.md + .claude/rules/module-quality.md
8 dimensions (D1-D8, including Practitioner Depth), each scored 1-5.

Usage:
    .venv/bin/python scripts/score_module.py 4 5 4 4 5 4 4 4
    .venv/bin/python scripts/score_module.py 4 5 4 4 5 4 4 4 --json
    echo "4 5 4 4 5 4 4 4" | .venv/bin/python scripts/score_module.py -

Dimensions (in order):
    D1: Learning Outcomes
    D2: Scaffolding & Structure
    D3: Active Learning
    D4: Real-World Connection
    D5: Assessment Alignment
    D6: Cognitive Load Management
    D7: Engagement & Motivation
    D8: Practitioner Depth (complexity-scaled)

Rules:
    - Every dimension must be >= 4 (a 3 anywhere = FAIL)
    - Sum must be >= 33 out of 40
    - Both conditions must pass

Rating bands derive from the dimension count n (per-dimension range 1-5):
    Pass:         4*n+1 .. 5*n   (33-40 for n=8)
    Needs polish: 3*n+1 .. 4*n   (25-32)
    Needs work:   2*n+1 .. 3*n   (17-24)
    Rewrite:      n     .. 2*n   (8-16)
"""

import json
import sys

DIMENSIONS = [
    "Learning Outcomes",
    "Scaffolding & Structure",
    "Active Learning",
    "Real-World Connection",
    "Assessment Alignment",
    "Cognitive Load Management",
    "Engagement & Motivation",
    "Practitioner Depth",
]

N_DIMS = len(DIMENSIONS)
SCORE_MIN = 1
SCORE_MAX = 5
FLOOR = 4
MAX_SUM = SCORE_MAX * N_DIMS
PASS_SUM = FLOOR * N_DIMS + 1

# Bands derived from the dimension count, not hard-coded totals.
RATINGS = [
    (4 * N_DIMS + 1, 5 * N_DIMS, "Pass"),
    (3 * N_DIMS + 1, 4 * N_DIMS, "Needs polish"),
    (2 * N_DIMS + 1, 3 * N_DIMS, "Needs work"),
    (N_DIMS, 2 * N_DIMS, "Rewrite"),
]


def score(values: list[int]) -> dict:
    if len(values) != N_DIMS:
        raise ValueError(f"Expected {N_DIMS} scores, got {len(values)}")

    for i, v in enumerate(values):
        if not SCORE_MIN <= v <= SCORE_MAX:
            raise ValueError(
                f"D{i+1} ({DIMENSIONS[i]}): score {v} out of range {SCORE_MIN}-{SCORE_MAX}"
            )

    total = sum(values)
    minimum = min(values)
    floor_pass = minimum >= FLOOR
    sum_pass = total >= PASS_SUM

    # Find rating tier by sum
    rating = "Unknown"
    for lo, hi, label in RATINGS:
        if lo <= total <= hi:
            rating = label
            break

    # Overall pass requires BOTH conditions
    passes = floor_pass and sum_pass

    # Find weak dimensions
    weak = [(DIMENSIONS[i], v) for i, v in enumerate(values) if v < FLOOR]

    return {
        "scores": {DIMENSIONS[i]: v for i, v in enumerate(values)},
        "sum": total,
        "max": MAX_SUM,
        "min_score": minimum,
        "floor_pass": floor_pass,
        "sum_pass": sum_pass,
        "passes": passes,
        "rating": rating if passes else f"FAIL ({rating} by sum, but floor violated)" if not floor_pass else f"FAIL ({rating})",
        "weak_dimensions": weak,
    }


def main():
    use_json = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--json"]

    if not args or args[0] == "-":
        raw = sys.stdin.read().strip()
        values = [int(x) for x in raw.split()]
    else:
        values = [int(x) for x in args]

    try:
        result = score(values)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if use_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["passes"] else 1)

    # Pretty output
    print()
    for dim, val in result["scores"].items():
        marker = " " if val >= FLOOR else " <-- BELOW FLOOR"
        print(f"  D{list(result['scores'].keys()).index(dim)+1}: {val}/5  {dim}{marker}")

    print(f"\n  Sum: {result['sum']}/{result['max']}")
    print(f"  Min: {result['min_score']}")
    print(f"  Floor (all >= {FLOOR}): {'PASS' if result['floor_pass'] else 'FAIL'}")
    print(f"  Sum (>= {PASS_SUM}):      {'PASS' if result['sum_pass'] else 'FAIL'}")

    if result["passes"]:
        print(f"\n  RESULT: PASS ({result['sum']}/{result['max']})")
    else:
        print("\n  RESULT: FAIL")
        if result["weak_dimensions"]:
            print(f"  Fix: {', '.join(f'{d} ({v})' for d, v in result['weak_dimensions'])}")
        if not result["sum_pass"]:
            print(f"  Need {PASS_SUM - result['sum']} more points to reach {PASS_SUM}")

    print()
    sys.exit(0 if result["passes"] else 1)


if __name__ == "__main__":
    main()
