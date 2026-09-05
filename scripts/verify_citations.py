#!/usr/bin/env python3
"""Gate B — semantic verification of citation seeds.

For each supported/weak_anchor claim in a seed, a verifier LLM reads the
cached URL page text and returns a per-claim verdict:

    SUPPORTED / UNSUPPORTED / CONTRADICTED / UNREADABLE

Cache inputs are read offline without refetching source content. Semantic
review may call the configured provider; this cache-integrity gate does not
establish provider identity or author/reviewer independence.

Usage:
    python scripts/verify_citations.py <module-key>
    python scripts/verify_citations.py <module-key> --agent codex
    python scripts/verify_citations.py <module-key> --dry-run
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citation_backfill import (  # type: ignore
    CITED_DISPOSITIONS,
    DOCS_ROOT,
    REPO_ROOT,
    dispatch_agy,
    dispatch_codex,
    load_section_pool,
    parse_agent_response,
    resolve_claim_source_urls,
    resolve_module_path,
    seed_path_for,
)
from fetch_citation import cached_text_path  # type: ignore

VERDICT_DIR = REPO_ROOT / ".pipeline" / "citation-verdicts"
MAX_PAGE_CHARS = 40_000


VERIFY_PROMPT_TEMPLATE = """You are the citation-verification gate of the
KubeDojo content pipeline. A claim was extracted from a module and paired
with a URL by a research step. Your job is to read the cached text of that
URL and decide whether the URL actually supports the claim.

## Rules

- `SUPPORTED` — the page directly or clearly states the claim. A reasonable
  reader could point at a specific passage.
- `UNSUPPORTED` — the page is topically related but does not state or
  confirm the specific claim (e.g., a general "windows on k8s" page cited
  for "kubelet on Windows uses X by default since 1.27").
- `CONTRADICTED` — the page states something that contradicts the claim
  (wrong number, wrong dates, wrong capability).
- `UNREADABLE` — the cached text is too short, non-English, or obviously
  failed extraction so you cannot judge.

Be strict: a URL that's "in the neighborhood" but doesn't actually back
the specific claim is UNSUPPORTED, not SUPPORTED. Quote a short supporting
passage in `evidence` when verdict is SUPPORTED (max ~200 chars).

## Output

Return ONE JSON object, no preamble, no markdown fences:

{{
  "verdict": "SUPPORTED" | "UNSUPPORTED" | "CONTRADICTED" | "UNREADABLE",
  "evidence": "<short quote from page, or null>",
  "reason": "<one short sentence>"
}}

## Claim

{claim_text}

## Claim class

{claim_class}

## Proposed URL

{url}

## Cached page text (up to ~{max_chars} characters, may be truncated)

{page_text}

Return the JSON now.
"""


def build_verify_prompt(claim_text: str, claim_class: str,
                        url: str, page_text: str) -> str:
    if len(page_text) > MAX_PAGE_CHARS:
        page_text = page_text[:MAX_PAGE_CHARS] + "\n\n[... truncated ...]"
    return VERIFY_PROMPT_TEMPLATE.format(
        claim_text=claim_text, claim_class=claim_class or "unknown",
        url=url, page_text=page_text, max_chars=MAX_PAGE_CHARS,
    )


def _read_cached_source(url: str) -> dict[str, Any]:
    text_path = cached_text_path(url)
    meta_path = text_path.with_suffix(".json")
    if not text_path.exists():
        return {"error": "cache_text_missing"}
    if not meta_path.exists():
        return {"error": "cache_metadata_missing"}
    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"error": "cache_metadata_malformed"}
    if not isinstance(metadata, dict):
        return {"error": "cache_metadata_not_object"}

    required = ("url", "final_url", "status", "issues", "truncated",
                "text_sha256", "text_bytes", "fetch_attempt_completed_at")
    missing = next((key for key in required if key not in metadata), None)
    if missing:
        return {"error": f"cache_metadata_missing_{missing}"}
    if metadata["url"] != url:
        return {"error": "cache_source_url_mismatch"}
    final_url = metadata["final_url"]
    if not isinstance(final_url, str) or not final_url:
        return {"error": "cache_final_url_invalid"}
    status = metadata["status"]
    if not isinstance(status, int) or isinstance(status, bool):
        return {"error": "cache_status_invalid"}
    if status < 200 or status >= 400:
        return {"error": f"cache_http_status_{status}"}
    issues = metadata["issues"]
    if not isinstance(issues, list):
        return {"error": "cache_issues_invalid"}
    if issues:
        return {"error": "cache_issues:" + ",".join(map(str, issues))}
    if metadata["truncated"] is not False:
        return {"error": "cache_text_truncated"}
    digest = metadata["text_sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or any(
        char not in "0123456789abcdef" for char in digest
    ):
        return {"error": "cache_text_sha256_invalid"}
    byte_count = metadata["text_bytes"]
    if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
        return {"error": "cache_text_bytes_invalid"}
    completed_at = metadata["fetch_attempt_completed_at"]
    if not isinstance(completed_at, str) or not completed_at:
        return {"error": "cache_fetch_attempt_completed_at_missing"}
    try:
        _dt.datetime.fromisoformat(completed_at)
    except ValueError:
        return {"error": "cache_fetch_attempt_completed_at_invalid"}
    try:
        body = text_path.read_bytes()
    except OSError:
        return {"error": "cache_text_unreadable"}
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return {"error": "cache_text_invalid_utf8"}
    if hashlib.sha256(body).hexdigest() != digest:
        return {"error": "cache_text_sha256_mismatch"}
    if len(body) != byte_count:
        return {"error": "cache_text_bytes_mismatch"}
    return {
        "text": text,
        "source_url": url,
        "final_url": final_url,
        "text_sha256": digest,
        "text_bytes": byte_count,
        "fetch_attempt_completed_at": completed_at,
    }


def load_page_text(url: str) -> str | None:
    """Return validated cached text without fetching or repairing cache state."""
    record = _read_cached_source(url)
    return record.get("text") if "text" in record else None


def _verdict_provenance(record: dict[str, Any], prompt: str,
                        page_text: str) -> dict[str, Any]:
    source_chars = len(page_text)
    clipped_chars = max(source_chars - MAX_PAGE_CHARS, 0)
    return {
        "source_url": record["source_url"],
        "final_url": record["final_url"],
        "text_sha256": record["text_sha256"],
        "text_bytes": record["text_bytes"],
        "fetch_attempt_completed_at": record["fetch_attempt_completed_at"],
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "source_text_clipped": bool(clipped_chars),
        "source_text_chars": source_chars,
        "source_text_chars_used": min(source_chars, MAX_PAGE_CHARS),
        "source_text_chars_clipped": clipped_chars,
    }


def verify_claim(claim: dict[str, Any], *, agent: str,
                 module_key: str,
                 section_pool: dict[str, Any] | None = None) -> dict[str, Any]:
    claim_id = claim.get("claim_id") or "?"
    urls = resolve_claim_source_urls(claim, section_pool=section_pool)
    url = urls[0].strip() if urls else ""
    claim_text = claim.get("claim_text") or ""
    claim_class = claim.get("claim_class") or ""
    if not url or not claim_text:
        return {"claim_id": claim_id, "verdict": "UNREADABLE",
                "reason": "missing_url_or_claim_text"}
    cached = _read_cached_source(url)
    if "error" in cached:
        return {"claim_id": claim_id, "verdict": "UNREADABLE",
                "reason": cached["error"]}
    page_text = cached["text"]
    if len(page_text) < 200:
        return {"claim_id": claim_id, "verdict": "UNREADABLE",
                "reason": f"cached_text_missing_or_too_short"
                          f"({len(page_text)})"}
    prompt = build_verify_prompt(claim_text, claim_class, url, page_text)
    provenance = _verdict_provenance(cached, prompt, page_text)
    base = {"claim_id": claim_id, "url": url, **provenance}
    ts = _dt.datetime.now(_dt.UTC).strftime("%H%M%SZ")
    task_id = f"verify-{module_key.replace('/', '-')}-{claim_id}-{ts}"
    if agent == "codex":
        ok, raw = dispatch_codex(prompt, task_id=task_id)
    elif agent == "agy":
        ok, raw = dispatch_agy(prompt)
    else:
        return {**base, "verdict": "UNREADABLE",
                "reason": f"unknown_agent:{agent}"}
    if not ok:
        return {**base, "verdict": "UNREADABLE",
                "reason": f"dispatch_failed:{raw[-200:]}"}
    try:
        parsed = parse_agent_response(raw)
    except Exception as exc:  # noqa: BLE001
        return {**base, "verdict": "UNREADABLE",
                "reason": f"parse_failed:{exc}",
                "raw_tail": raw[-200:]}
    parsed.update(base)
    return parsed


def run_verify(module_key: str, *, agent: str = "agy",
               dry_run: bool = False) -> dict[str, Any]:
    module_path = resolve_module_path(module_key)
    normalized_key = module_path.relative_to(DOCS_ROOT).with_suffix("").as_posix()
    seed_path = seed_path_for(normalized_key)
    if not seed_path.exists():
        return {"module_key": normalized_key, "ok": False,
                "error": "no_seed_file"}
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    section_pool = load_section_pool(seed.get("section_pool_ref"))
    claims_to_verify = [
        c for c in seed.get("claims") or []
        if c.get("disposition") in CITED_DISPOSITIONS
        and resolve_claim_source_urls(c, section_pool=section_pool)
    ]
    if dry_run:
        return {"module_key": normalized_key, "dry_run": True,
                "claim_count": len(claims_to_verify),
                "claim_ids": [c.get("claim_id") for c in claims_to_verify]}

    verdicts = []
    for claim in claims_to_verify:
        verdicts.append(verify_claim(claim, agent=agent,
                                     module_key=normalized_key,
                                     section_pool=section_pool))

    counts = {"SUPPORTED": 0, "UNSUPPORTED": 0,
              "CONTRADICTED": 0, "UNREADABLE": 0}
    for v in verdicts:
        counts[v.get("verdict", "UNREADABLE")] = \
            counts.get(v.get("verdict", "UNREADABLE"), 0) + 1

    VERDICT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = VERDICT_DIR / f"{normalized_key.replace('/', '-')}.json"
    out_path.write_text(json.dumps({
        "module_key": normalized_key,
        "verifier_agent": agent,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "counts": counts,
        "verdicts": verdicts,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {"module_key": normalized_key, "ok": True,
            "counts": counts,
            "verdict_path": str(out_path.relative_to(REPO_ROOT)),
            "failing_count": counts.get("UNSUPPORTED", 0)
                            + counts.get("CONTRADICTED", 0)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gate B — semantic verification")
    p.add_argument("module_key")
    p.add_argument("--agent", default="agy", choices=["codex", "agy"])
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    result = run_verify(args.module_key, agent=args.agent, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") or result.get("dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
