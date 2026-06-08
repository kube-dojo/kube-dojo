#!/usr/bin/env python3
"""Context-integrity canary — a DETERMINISTIC brain-rot monitor for long sessions.

Ported from learn-ukrainian (scripts/context_canary.py, 2026-06-08) to KubeDojo.

Why this exists
---------------
With autocompact disabled, a single Claude Code session can grow to 700K-1M tokens.
Long-context retrieval degrades ("brain rot") well before the model *notices* — a
dropped instruction or a misremembered SHA is invisible from the inside, because the
model does not reliably self-report rot. Trusting a self-assessment ("I feel fine")
is exactly the failure mode. So we measure instead.

How it works
------------
1. `mint`  — freeze K anchors as (id, question, ground-truth answer). The truth is
             captured EARLY (low context, presumed clean) from real state, then frozen.
             REFINEMENT (learn-ukrainian 2026-06-08): mint ONLY IMMUTABLE anchors
             (merged SHAs, PR/issue numbers, locked decisions) — a fact that changes
             mid-session scores as "drift" when it is merely stale, not rot.
2. ...time passes, context grows...
3. `score` — the agent answers the same questions FROM MEMORY/CONTEXT (no scrolling
             back to re-read), writes them to a JSON, and this script diffs them against
             the frozen truth. The SCRIPT computes the match — the agent cannot grade
             itself into a pass. Drift below threshold => hand off NOW, regardless of
             the token count.
4. Each score appends a (context_tokens, score) row to a CSV so we can MAP where rot
   starts for this model on this session shape across runs.

Usage
-----
  context_canary.py mint  --facts facts.json --out probe.json
  context_canary.py score --probe probe.json --answers answers.json \
                          --context-tokens 500000 --model claude-opus-4-8 --log canary_log.csv

`facts.json`   : [{"id": "...", "q": "...", "a": "..."}, ...]
`answers.json` : {"<id>": "<answer-from-memory>", ...}

Exit code: 0 if PASS, 2 if FAIL (hand off), 1 on usage error.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import sys
from pathlib import Path


def _norm(value: object) -> str:
    """Whitespace/case-insensitive normalization for fuzzy comparison."""
    return " ".join(str(value).strip().lower().split())


def _similarity(truth: str, got: str) -> float:
    return difflib.SequenceMatcher(None, _norm(truth), _norm(got)).ratio()


def cmd_mint(args: argparse.Namespace) -> int:
    facts = json.loads(Path(args.facts).read_text(encoding="utf-8"))
    if not isinstance(facts, list) or not facts:
        print(
            "error: --facts must be a non-empty JSON list of {id,q,a}", file=sys.stderr
        )
        return 1
    ids = [f.get("id") for f in facts]
    if len(set(ids)) != len(ids) or not all(ids):
        print("error: every fact needs a unique non-empty 'id'", file=sys.stderr)
        return 1
    probe = {"anchors": [{"id": f["id"], "q": f["q"], "a": f["a"]} for f in facts]}
    Path(args.out).write_text(
        json.dumps(probe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"minted {len(facts)} anchors -> {args.out}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    probe = json.loads(Path(args.probe).read_text(encoding="utf-8"))
    answers = json.loads(Path(args.answers).read_text(encoding="utf-8"))
    anchors = probe.get("anchors", [])
    if not anchors:
        print("error: probe has no anchors", file=sys.stderr)
        return 1

    correct = 0
    rows = []
    for anchor in anchors:
        aid = anchor["id"]
        truth = anchor["a"]
        got = answers.get(aid, "")
        sim = _similarity(truth, got)
        ok = sim >= args.threshold
        correct += 1 if ok else 0
        rows.append((aid, ok, sim, anchor["q"]))

    k = len(anchors)
    score = correct / k
    for aid, ok, sim, q in rows:
        tag = "PASS " if ok else "DRIFT"
        print(f"  [{tag}] {aid} (sim={sim:.2f}) {q}")
        if not ok:
            print(
                f"          truth: {next(a['a'] for a in anchors if a['id'] == aid)!r}"
            )
            print(f"          got  : {answers.get(aid, '')!r}")

    verdict = "PASS" if score >= args.pass_ratio else "FAIL-HANDOFF"
    print(f"SCORE {correct}/{k} = {score:.2f}  ->  {verdict}")

    if args.log:
        log_path = Path(args.log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not log_path.exists()
        with log_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if is_new:
                writer.writerow(
                    ["context_tokens", "model", "k", "correct", "score", "verdict"]
                )
            writer.writerow(
                [args.context_tokens, args.model, k, correct, f"{score:.3f}", verdict]
            )

    return 0 if verdict == "PASS" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    mint = sub.add_parser("mint", help="Freeze ground-truth anchors into a probe file.")
    mint.add_argument("--facts", required=True, help="JSON list of {id,q,a}")
    mint.add_argument("--out", required=True, help="Probe output path")
    mint.set_defaults(func=cmd_mint)

    score = sub.add_parser(
        "score", help="Diff from-memory answers against the frozen probe."
    )
    score.add_argument("--probe", required=True)
    score.add_argument("--answers", required=True, help="JSON {id: answer}")
    score.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Per-anchor similarity to count as recalled (default 0.75)",
    )
    score.add_argument(
        "--pass-ratio",
        type=float,
        default=0.85,
        help="Fraction of anchors that must pass (default 0.85)",
    )
    score.add_argument(
        "--context-tokens",
        type=int,
        default=0,
        help="Context size at probe time (for the log)",
    )
    score.add_argument("--model", default="unknown")
    score.add_argument(
        "--log", help="CSV to append the (context_tokens, score) data point"
    )
    score.set_defaults(func=cmd_score)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
