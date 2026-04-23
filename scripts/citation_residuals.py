#!/usr/bin/env python3
"""Auto-resolver for citation residuals filed by pipeline_v4 Stage 4.

Reads `.pipeline/v3/human-review/<module>.json`, resolves the
`queued_findings.needs_citation[]` entries by asking a small LLM for
candidate URLs, validating each via `fetch_citation`, and appending the
accepted URL to the module's `## Sources` section. Unresolved findings
move to `unresolvable_findings[]` so re-runs are idempotent.

See GH #343 for the spec and #341 for the parent epic.

Scope (#343 phase-1):
    - Processes `needs_citation` findings only.
    - Does NOT touch `overstated_unfixed`, `off_topic_unfixed`,
      `overstatement_queued`, `off_topic_delete_queued` — those are #344.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import fetch_citation  # noqa: E402
from citation_backfill import dispatch_gemini, parse_agent_response  # noqa: E402

HUMAN_REVIEW_DIR = REPO_ROOT / ".pipeline" / "v3" / "human-review"
DEFAULT_MAX_CANDIDATES = 3
MIN_SIGNAL_ANCHORS_REQUIRED = 1


# ---- IO ------------------------------------------------------------------


def load_queue_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_queue_file(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def module_path_from_key(module_key: str) -> Path:
    return REPO_ROOT / "src" / "content" / "docs" / (module_key + ".md")


# ---- signal extraction ---------------------------------------------------


_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_PRICE_RE = re.compile(
    r"\$\s*[\d,.]+\s*(?:billion|million|thousand|[bmk])?",
    re.IGNORECASE,
)
_PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*%")


def extract_anchors(excerpt: str, signals: list[str]) -> list[str]:
    """Pick concrete substrings from `excerpt` that a source page must
    contain to validate the citation.

    Mirrors the signal taxonomy emitted by citation_v3. Anchors are the
    *values* (e.g. "2014", "$6.5 billion") not the category names.
    """
    anchors: list[str] = []
    signal_set = set(signals)
    if "dated_year" in signal_set or "year_reference" in signal_set:
        anchors.extend(m.group(0) for m in _YEAR_RE.finditer(excerpt))
    if "price_usd" in signal_set or "dollar_amount" in signal_set:
        anchors.extend(m.group(0).strip() for m in _PRICE_RE.finditer(excerpt))
    if "percentage" in signal_set:
        anchors.extend(m.group(0).strip() for m in _PERCENT_RE.finditer(excerpt))
    # Deduplicate while preserving order.
    seen: set[str] = set()
    result: list[str] = []
    for a in anchors:
        key = a.lower()
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result


def anchors_present_in_text(anchors: list[str], text: str) -> list[str]:
    if not anchors:
        return []
    text_lower = text.lower()
    return [a for a in anchors if a.lower() in text_lower]


# ---- candidate discovery -------------------------------------------------


CANDIDATE_PROMPT = """You are helping cite a factual claim in a technical curriculum module.

The claim (from the module):
---
{excerpt}
---

Signals the fact-checker flagged: {signals}
Search hints prepared by the fact-checker:
{hints}

HARD CONSTRAINT — the pipeline's deterministic gate ONLY accepts URLs whose
host is on this exact allowlist:

{allowlist}

Any URL whose host is not on that list will be rejected before the content is
even checked. Press domains like reuters.com, bbc.com, theverge.com,
theguardian.com, wired.com are NOT on the allowlist — do not suggest them.

For this type of claim, the most commonly useful hosts are:
  - en.wikipedia.org for named incidents, acquisitions, public events where
    no primary source is available.
  - the vendor's own .com for vendor-published claims about their own
    product/outage/acquisition.
  - standards/upstream docs for capability claims about specific tools.

Return 1-3 candidate URLs that (a) are on the allowlist above AND (b) you have
high confidence actually discuss the specific claim — same year, same dollar
figure, same named incident/company. Do not invent URLs. If no allowlist URL
plausibly covers the claim, return an empty list.

Respond with strict JSON, no prose, no code fences:
{{
  "candidates": [
    {{"url": "https://...", "tier": "standards|upstream|vendor|incidents|general", "why": "one sentence"}},
    ...
  ]
}}
"""


def _format_allowlist_for_prompt() -> str:
    """Render the yaml allowlist as a flat, prompt-friendly list so the LLM
    can actually comply with the constraint."""
    import yaml

    try:
        raw = yaml.safe_load(
            (REPO_ROOT / "docs" / "citation-trusted-domains.yaml").read_text(encoding="utf-8")
        )
    except (OSError, yaml.YAMLError):
        return "  (allowlist unreadable; reject everything)"
    tiers = raw.get("tiers") or {}
    lines: list[str] = []
    for tier_name, domains in tiers.items():
        clean = [str(d).split("#", 1)[0].strip() for d in (domains or [])]
        clean = [d for d in clean if d]
        if clean:
            lines.append(f"  {tier_name}: {', '.join(clean)}")
    return "\n".join(lines)


def build_candidate_prompt(finding: dict[str, Any]) -> str:
    hints = finding.get("search_hint") or []
    hint_lines = "\n".join(f"  - {h}" for h in hints) if hints else "  (none)"
    return CANDIDATE_PROMPT.format(
        excerpt=finding.get("excerpt", "").strip(),
        signals=", ".join(finding.get("signals") or []) or "(none)",
        hints=hint_lines,
        allowlist=_format_allowlist_for_prompt(),
    )


def request_candidates(
    finding: dict[str, Any],
    *,
    dispatcher=dispatch_gemini,
) -> list[dict[str, Any]]:
    """Ask the LLM for candidate URLs. Returns a list of dicts with
    ``url``, ``tier``, ``why``. Empty list on any failure (the caller
    marks the finding unresolvable)."""
    prompt = build_candidate_prompt(finding)
    ok, raw = dispatcher(prompt)
    if not ok:
        return []
    try:
        parsed = parse_agent_response(raw)
    except (ValueError, json.JSONDecodeError):
        return []
    candidates = parsed.get("candidates")
    if not isinstance(candidates, list):
        return []
    valid: list[dict[str, Any]] = []
    for c in candidates[:DEFAULT_MAX_CANDIDATES]:
        if not isinstance(c, dict):
            continue
        url = str(c.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        valid.append(
            {
                "url": url,
                "tier": str(c.get("tier") or "unknown"),
                "why": str(c.get("why") or "").strip(),
            }
        )
    return valid


# ---- validation ----------------------------------------------------------


def validate_candidate(
    candidate: dict[str, Any],
    finding: dict[str, Any],
    *,
    fetcher=fetch_citation.fetch,
    cached_text_path=fetch_citation.cached_text_path,
) -> dict[str, Any]:
    """Fetch a candidate URL and check it against the finding's signals.

    Returns a dict with either ``ok: True`` (and page metadata) or
    ``ok: False`` with a ``reason`` string.
    """
    url = candidate["url"]
    try:
        meta = fetcher(url)
    except Exception as exc:  # noqa: BLE001 — network errors are expected
        return {"ok": False, "url": url, "reason": f"fetch_raised:{type(exc).__name__}"}
    status = int(meta.get("status") or 0)
    if status != 200:
        return {"ok": False, "url": url, "reason": f"http_{status}"}
    tier = meta.get("allowlist_tier")
    if not tier:
        return {"ok": False, "url": url, "reason": "off_allowlist"}
    text_path = cached_text_path(url)
    try:
        body = text_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"ok": False, "url": url, "reason": "cache_read_failed"}
    anchors = extract_anchors(
        finding.get("excerpt", ""),
        finding.get("signals") or [],
    )
    matched = anchors_present_in_text(anchors, body)
    if anchors and len(matched) < MIN_SIGNAL_ANCHORS_REQUIRED:
        return {
            "ok": False,
            "url": url,
            "reason": "no_anchor_match",
            "anchors_expected": anchors,
            "anchors_matched": matched,
        }
    return {
        "ok": True,
        "url": url,
        "final_url": meta.get("final_url", url),
        "tier": tier,
        "anchors_matched": matched,
        "page_bytes": meta.get("bytes", 0),
    }


# ---- injection into module --------------------------------------------------


_SOURCES_HEADER_RE = re.compile(r"^## Sources\s*$", re.MULTILINE)


def short_id_for(url: str) -> str:
    return "res-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]


def build_source_line(url: str, finding: dict[str, Any], *, title: str | None = None) -> str:
    """Render one `- [title](url) — note` bullet for the Sources list."""
    display_title = title or _derive_title_from_url(url)
    note = _summarize_finding(finding)
    safe_title = display_title.replace("[", r"\[").replace("]", r"\]")
    return f"- [{safe_title}]({url}) — {note}"


def _derive_title_from_url(url: str) -> str:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = (parsed.hostname or "").removeprefix("www.")
    path_segments = [seg for seg in parsed.path.split("/") if seg]
    tail = path_segments[-1] if path_segments else ""
    readable = tail.replace("-", " ").replace("_", " ").strip()
    if host and readable:
        return f"{host}: {readable}"
    return host or url


def _summarize_finding(finding: dict[str, Any]) -> str:
    excerpt = (finding.get("excerpt") or "").strip()
    # First sentence of excerpt, capped at 160 chars — enough for context
    # without duplicating the whole paragraph.
    first_sentence = re.split(r"(?<=[.!?])\s+", excerpt, maxsplit=1)[0]
    summary = first_sentence[:160].strip()
    if not summary:
        return "Supporting citation for the flagged claim."
    if not summary.endswith((".", "!", "?")):
        summary += "."
    return summary


def inject_source(module_text: str, source_line: str) -> tuple[str, bool]:
    """Append ``source_line`` to the module's ``## Sources`` section.

    Creates the section if missing. Idempotent: if the exact line is
    already present, returns ``(original, False)``.
    """
    if source_line in module_text:
        return module_text, False
    if _SOURCES_HEADER_RE.search(module_text):
        # Append inside the existing Sources section. The section
        # conventionally sits at end-of-file with only trailing newlines,
        # so appending at the end of the file keeps it alphabetical-free
        # but monotonically ordered (matches existing batch-c style).
        trimmed = module_text.rstrip("\n")
        return trimmed + "\n" + source_line + "\n", True
    # No Sources section yet — create one.
    trimmed = module_text.rstrip("\n")
    return trimmed + "\n\n## Sources\n\n" + source_line + "\n", True


# ---- per-module resolver -------------------------------------------------


def resolve_module(
    queue_path: Path,
    *,
    dry_run: bool = False,
    dispatcher=dispatch_gemini,
    fetcher=fetch_citation.fetch,
    cached_text_path=fetch_citation.cached_text_path,
) -> dict[str, Any]:
    """Resolve all `needs_citation` findings for one module.

    Returns a stats dict:
        {
          "module_key": str,
          "considered": int,
          "resolved": int,
          "unresolvable": int,
          "skipped_already_resolved": int,
          "module_edited": bool,
        }
    """
    data = load_queue_file(queue_path)
    module_key = data.get("module_key") or queue_path.stem
    queued = data.setdefault("queued_findings", {})
    needs_citation: list[dict[str, Any]] = list(queued.get("needs_citation") or [])
    resolved_list: list[dict[str, Any]] = list(data.setdefault("resolved_findings", []))
    unresolvable_list: list[dict[str, Any]] = list(
        data.setdefault("unresolvable_findings", [])
    )

    module_path = module_path_from_key(module_key)
    if not module_path.exists():
        return {
            "module_key": module_key,
            "considered": 0,
            "resolved": 0,
            "unresolvable": 0,
            "skipped_already_resolved": 0,
            "module_edited": False,
            "error": "module_not_found",
        }

    module_text = module_path.read_text(encoding="utf-8")
    module_dirty = False

    still_pending: list[dict[str, Any]] = []
    stats = {
        "module_key": module_key,
        "considered": len(needs_citation),
        "resolved": 0,
        "unresolvable": 0,
        "skipped_already_resolved": 0,
        "module_edited": False,
    }

    for finding in needs_citation:
        candidates = request_candidates(finding, dispatcher=dispatcher)
        if not candidates:
            finding_record = dict(finding)
            finding_record["unresolvable_reason"] = "no_candidates_returned"
            finding_record["resolved_at"] = _now_iso()
            unresolvable_list.append(finding_record)
            stats["unresolvable"] += 1
            continue

        accepted: dict[str, Any] | None = None
        attempts: list[dict[str, Any]] = []
        for candidate in candidates:
            validation = validate_candidate(
                candidate,
                finding,
                fetcher=fetcher,
                cached_text_path=cached_text_path,
            )
            attempts.append({"candidate": candidate, "validation": validation})
            if validation.get("ok"):
                accepted = {"candidate": candidate, "validation": validation}
                break

        if accepted is None:
            finding_record = dict(finding)
            finding_record["unresolvable_reason"] = "all_candidates_failed"
            finding_record["attempts"] = attempts
            finding_record["resolved_at"] = _now_iso()
            unresolvable_list.append(finding_record)
            stats["unresolvable"] += 1
            continue

        url = accepted["validation"]["final_url"]
        source_line = build_source_line(url, finding)
        if dry_run:
            _, injected = inject_source(module_text, source_line)
            stats["resolved"] += 1
            still_pending.append(
                {
                    **finding,
                    "_dry_run_proposed": {
                        "url": url,
                        "source_line": source_line,
                        "injected": injected,
                    },
                }
            )
            continue

        module_text, injected = inject_source(module_text, source_line)
        if not injected:
            stats["skipped_already_resolved"] += 1
        else:
            module_dirty = True

        resolved_list.append(
            {
                **finding,
                "resolved_at": _now_iso(),
                "url": url,
                "tier": accepted["validation"]["tier"],
                "short_id": short_id_for(url),
                "anchors_matched": accepted["validation"].get("anchors_matched", []),
            }
        )
        stats["resolved"] += 1

    if module_dirty:
        module_path.write_text(module_text, encoding="utf-8")
        stats["module_edited"] = True

    if not dry_run:
        queued["needs_citation"] = still_pending
        data["resolved_findings"] = resolved_list
        data["unresolvable_findings"] = unresolvable_list
        save_queue_file(queue_path, data)

    return stats


def _now_iso() -> str:
    import datetime as _dt

    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


# ---- bulk + report -------------------------------------------------------


def iter_queue_files() -> list[Path]:
    if not HUMAN_REVIEW_DIR.is_dir():
        return []
    return sorted(
        p for p in HUMAN_REVIEW_DIR.glob("*.json") if not p.name.endswith(".staging.json")
    )


def build_report() -> dict[str, Any]:
    files = iter_queue_files()
    totals: dict[str, int] = {
        "files": 0,
        "needs_citation": 0,
        "overstated_unfixed": 0,
        "off_topic_unfixed": 0,
        "resolved_findings": 0,
        "unresolvable_findings": 0,
    }
    per_file = []
    for f in files:
        try:
            data = load_queue_file(f)
        except Exception:  # noqa: BLE001 — skip malformed
            continue
        qf = data.get("queued_findings") or {}
        nc = len(qf.get("needs_citation") or [])
        ou = len(qf.get("overstated_unfixed") or [])
        ot = len(qf.get("off_topic_unfixed") or [])
        res = len(data.get("resolved_findings") or [])
        unres = len(data.get("unresolvable_findings") or [])
        totals["files"] += 1
        totals["needs_citation"] += nc
        totals["overstated_unfixed"] += ou
        totals["off_topic_unfixed"] += ot
        totals["resolved_findings"] += res
        totals["unresolvable_findings"] += unres
        per_file.append(
            {
                "file": f.name,
                "needs_citation": nc,
                "overstated_unfixed": ou,
                "off_topic_unfixed": ot,
                "resolved": res,
                "unresolvable": unres,
            }
        )
    return {"totals": totals, "files": per_file}


# ---- CLI ------------------------------------------------------------------


def _queue_path_for(module_key: str) -> Path:
    # Turn "ai-ml-engineering/advanced-genai/module-1.1" style into the
    # flat slash-free filename used in .pipeline/v3/human-review/.
    slug = module_key.replace("/", "-")
    direct = HUMAN_REVIEW_DIR / f"{slug}.json"
    if direct.exists():
        return direct
    # Fallback: substring match.
    matches = [p for p in iter_queue_files() if slug in p.stem]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(f"No queue file found for module_key={module_key!r}")
    raise SystemExit(
        f"Ambiguous module_key={module_key!r}; matches: {[p.name for p in matches]}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_report = sub.add_parser("report", help="Summarize the residuals queue")
    p_report.add_argument("--json", action="store_true", help="Emit JSON to stdout")

    p_resolve = sub.add_parser("resolve", help="Resolve needs_citation findings")
    p_resolve.add_argument(
        "module_key",
        nargs="?",
        help="Module key or slug. Use --all instead to process every queued file.",
    )
    p_resolve.add_argument("--all", action="store_true", help="Process every queue file")
    p_resolve.add_argument(
        "--dry-run",
        action="store_true",
        help="Propose resolutions but do not write to modules or queue JSON",
    )

    args = parser.parse_args(argv)

    if args.command == "report":
        report = build_report()
        if args.json:
            print(json.dumps(report, indent=2))
            return 0
        t = report["totals"]
        print(f"Files: {t['files']}")
        print(f"needs_citation open:   {t['needs_citation']}")
        print(f"overstated_unfixed:    {t['overstated_unfixed']}  (out of scope for #343)")
        print(f"off_topic_unfixed:     {t['off_topic_unfixed']}   (out of scope for #343)")
        print(f"resolved_findings:     {t['resolved_findings']}")
        print(f"unresolvable_findings: {t['unresolvable_findings']}")
        return 0

    if args.command == "resolve":
        if args.all:
            targets = iter_queue_files()
        else:
            if not args.module_key:
                parser.error("resolve requires either <module_key> or --all")
            targets = [_queue_path_for(args.module_key)]

        # Filter out files with no needs_citation entries — cheap early exit.
        useful_targets = []
        for t in targets:
            try:
                d = load_queue_file(t)
            except Exception:  # noqa: BLE001
                continue
            if (d.get("queued_findings") or {}).get("needs_citation"):
                useful_targets.append(t)

        if not useful_targets:
            print("No residuals with needs_citation findings.")
            return 0

        totals = {"considered": 0, "resolved": 0, "unresolvable": 0, "modules_edited": 0}
        for qp in useful_targets:
            t0 = time.time()
            stats = resolve_module(qp, dry_run=args.dry_run)
            totals["considered"] += stats["considered"]
            totals["resolved"] += stats["resolved"]
            totals["unresolvable"] += stats["unresolvable"]
            if stats.get("module_edited"):
                totals["modules_edited"] += 1
            print(
                f"{stats['module_key']}: "
                f"considered={stats['considered']} "
                f"resolved={stats['resolved']} "
                f"unresolvable={stats['unresolvable']} "
                f"edited={stats.get('module_edited')} "
                f"({time.time() - t0:.1f}s)"
            )
        print()
        print(
            f"TOTAL: considered={totals['considered']} "
            f"resolved={totals['resolved']} "
            f"unresolvable={totals['unresolvable']} "
            f"modules_edited={totals['modules_edited']}"
        )
        if totals["considered"]:
            rate = totals["resolved"] / totals["considered"] * 100
            print(f"Auto-resolve rate: {rate:.1f}%")
        return 0

    parser.error(f"Unknown command: {args.command}")  # unreachable; argparse exits above
    return 2  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
