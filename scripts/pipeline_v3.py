#!/usr/bin/env python3
"""Pipeline v3 — single-module end-to-end content gate orchestrator.

Stages, in order:
    1. research       (Codex)        — emit citation seed
    2. verify (B)     (Gemini)       — semantic check of every cited URL
    3. inject         (Codex)        — wrap citations + apply seed rewrites IN PLACE
    4. audit A/C/D    (Codex/Gemini) — overstatement, unsourced, coherence
    5. auto-apply                    — deterministic fixes for the gate findings
                                       we know how to apply without an LLM
    6. re-audit                      — run A/C/D again; queue residuals to
                                       .pipeline/v3/human-review/<key>.json

Exit code: 0 iff every stage cleared and the final re-audit was clean.
On failure, the run record at .pipeline/v3/runs/<key>.json carries the
detail so the orchestrator never streams raw LLM output through Claude
context.

Auto-apply policy (intentionally narrow in v3.0):
    Gate A overstated + suggested_rewrite      → substring swap
    Gate D off_topic + suggested_action=delete → drop the offending paragraph
Anything else (Gate D rewrite_to_fit, Gate C needs_citation) is queued.

Usage:
    python scripts/pipeline_v3.py <module-key>
    python scripts/pipeline_v3.py <module-key> --skip-research   # use existing seed
    python scripts/pipeline_v3.py <module-key> --no-auto-apply   # audit only
    python scripts/pipeline_v3.py <module-key> --gate-agent codex
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from citation_backfill import (  # type: ignore  # noqa: E402
    DOCS_ROOT, REPO_ROOT, resolve_module_path, run_inject, run_research,
    seed_path_for,
)
from check_coherence import check_coherence  # type: ignore  # noqa: E402
from check_overstatement import audit_file as audit_overstatement  # type: ignore  # noqa: E402
from check_unsourced import audit_file as audit_unsourced  # type: ignore  # noqa: E402
from verify_citations import run_verify  # type: ignore  # noqa: E402


V3_DIR = REPO_ROOT / ".pipeline" / "v3"
RUNS_DIR = V3_DIR / "runs"
HUMAN_REVIEW_DIR = V3_DIR / "human-review"
SUMMARY_PATH = V3_DIR / "summary.jsonl"


def _iso_utc() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


def _sources_only_fallback(module_key: str, module_path: Path,
                           inject_result: dict[str, Any]) -> dict[str, Any]:
    """When full inject fails on diff-lint, write just a ## Sources section.

    The full inject does three things: inline anchors, prose rewrites, and a
    Sources section from further_reading. The diff-lint bails the WHOLE
    inject on a single unauthorized prose change, losing even the Sources
    section — so the module stays at the citation-gate cap of 1.5.

    Fallback: if the seed has further_reading entries, skip inline + prose
    and just append a Sources section from further_reading. Lifts the module
    off the 1.5 cap without the risk of unauthorized prose rewrites.
    """
    result: dict[str, Any] = {"applied": False, "ok": False, "reason": None}
    # Only fallback if the full inject tripped diff-lint. Real failures
    # (dispatch error, parse error, nothing_to_do) should still abort.
    if not inject_result.get("diff_issues"):
        result["reason"] = "no_diff_issues_to_salvage"
        return result
    seed_path = seed_path_for(module_key)
    if not seed_path.exists():
        result["reason"] = "no_seed"
        return result
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    fr = seed.get("further_reading") or []
    if not fr:
        result["reason"] = "no_further_reading"
        return result
    body = module_path.read_text(encoding="utf-8")
    if re.search(r"^##+\s+sources\b", body, re.IGNORECASE | re.MULTILINE):
        # Already has a Sources section — don't duplicate.
        result["reason"] = "sources_section_already_present"
        return result
    lines = ["", "## Sources", ""]
    for link in fr:
        url = (link.get("url") or "").strip()
        title = (link.get("title") or url).strip()
        why = (link.get("why_relevant") or "").strip()
        if not url:
            continue
        if why:
            lines.append(f"- [{title}]({url}) — {why}")
        else:
            lines.append(f"- [{title}]({url})")
    if len(lines) <= 3:
        result["reason"] = "no_valid_further_reading"
        return result
    block = "\n".join(lines) + "\n"
    new_body = body.rstrip() + "\n" + block
    module_path.write_text(new_body, encoding="utf-8")
    result["applied"] = True
    result["ok"] = True
    result["further_reading_count"] = len(fr)
    return result


_SCHEMA_CLAIM_INDEX_RE = re.compile(r"^claim\[(\d+)\]:")


def _prune_schema_failed_claims(module_key: str, schema_issues: list[str]) -> dict[str, Any]:
    """Drop seed claims flagged by validate_seed so the pipeline can continue.

    Codex occasionally emits one bad claim (e.g. anchor_text containing a
    newline) out of many valid ones. The original abort-the-whole-module
    behavior wasted 10+ good claims + validated further_reading on a single
    bad entry. Prune just the offenders and continue.
    """
    result: dict[str, Any] = {"pruned_indices": [], "remaining_claims": 0,
                              "has_further_reading": False,
                              "non_claim_issues": []}
    bad_idx: set[int] = set()
    non_claim_issues: list[str] = []
    for issue in schema_issues:
        m = _SCHEMA_CLAIM_INDEX_RE.match(issue)
        if m:
            bad_idx.add(int(m.group(1)))
        else:
            non_claim_issues.append(issue)
    result["non_claim_issues"] = non_claim_issues
    # Always load the seed so the caller's "remaining citable content"
    # check reflects reality even when only non-claim issues were
    # emitted (e.g. missing_section_pool: a warning, but the claims
    # array is still valid). Previously this path returned
    # remaining_claims=0 unconditionally, which made the caller abort
    # modules with 10+ good claims + further_reading on any non-claim
    # schema warning — reversing the prune-and-continue intent.
    seed_path = seed_path_for(module_key)
    if not seed_path.exists():
        return result
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    claims = seed.get("claims") or []
    if bad_idx:
        kept = [c for i, c in enumerate(claims) if i not in bad_idx]
        seed["claims"] = kept
        seed_path.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        result["pruned_indices"] = sorted(bad_idx)
    else:
        kept = claims
    result["remaining_claims"] = len(kept)
    result["has_further_reading"] = bool(seed.get("further_reading") or [])
    return result


def _prune_failed_cited_claims(module_key: str, verdict_path_rel: str | None) -> dict[str, Any]:
    """Drop UNSUPPORTED/CONTRADICTED claims from the seed so inject can continue.

    Gate B (verify) rejects the specific citation URL the researcher proposed,
    not the underlying claim. The seed's further_reading entries stayed
    within the allowlist and passed HTTP validation independently, so inject
    can still write a Sources section even when every inline claim fails
    verify. This prune+continue beats bailing the whole module — the
    citation-gate cap stays at 1.5 otherwise.
    """
    result: dict[str, Any] = {"pruned_ids": [], "remaining_citable": 0,
                              "has_further_reading": False}
    if not verdict_path_rel:
        return result
    verdict_path = REPO_ROOT / verdict_path_rel
    if not verdict_path.exists():
        return result
    verdicts = json.loads(verdict_path.read_text(encoding="utf-8")).get("verdicts") or []
    fail_ids = {str(v.get("claim_id")) for v in verdicts
                if v.get("verdict") in ("UNSUPPORTED", "CONTRADICTED")}
    if not fail_ids:
        return result
    seed_path = seed_path_for(module_key)
    if not seed_path.exists():
        return result
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    kept: list[dict[str, Any]] = []
    pruned: list[str] = []
    for claim in seed.get("claims") or []:
        cid = str(claim.get("claim_id"))
        if cid in fail_ids and claim.get("disposition") in ("supported", "weak_anchor"):
            pruned.append(cid)
            continue
        kept.append(claim)
    seed["claims"] = kept
    seed_path.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    result["pruned_ids"] = pruned
    result["remaining_citable"] = sum(
        1 for c in kept if c.get("disposition") in ("supported", "weak_anchor")
    )
    result["has_further_reading"] = bool(seed.get("further_reading") or [])
    return result


# ---- audit pass -----------------------------------------------------------


def _audit_all(module_path: Path, *, gate_agent_text: str,
               gate_agent_coherence: str) -> dict[str, Any]:
    """Run Gates A, C, D against the current state of the module."""
    a = audit_overstatement(module_path, use_llm=True, agent=gate_agent_text)
    c = audit_unsourced(module_path, use_llm=True, agent=gate_agent_text)
    d = check_coherence(module_path, agent=gate_agent_coherence)
    return {"A_overstatement": a, "C_unsourced": c, "D_coherence": d}


def _audit_is_clean(audit: dict[str, Any]) -> bool:
    """A run is clean when every gate has zero actionable hits."""
    a_hits = [c for c in audit["A_overstatement"].get("candidates") or []
              if (c.get("verdict") or {}).get("verdict") == "overstated"]
    c_hits = [c for c in audit["C_unsourced"].get("candidates") or []
              if (c.get("verdict") or {}).get("verdict") == "needs_citation"]
    d_hits = [f for f in audit["D_coherence"].get("findings") or []
              if f.get("verdict") == "off_topic"]
    return not (a_hits or c_hits or d_hits)


# ---- auto-apply -----------------------------------------------------------


_SWAP_BREAKAGE_PATTERNS = (
    "..",          # double period from period-already-after-sentence
    " . ",         # orphan period left mid-line
    ". .",         # period followed by another period after a space
    "..`",         # broken backtick fragment after a swap
    "  ",          # accidental double space (only flagged in prose context)
)
_SENT_COUNT_RE = __import__("re").compile(r"[.!?](?=\s|$)")


def _swap_introduced_breakage(line: str) -> str | None:
    """Return a short reason string if the post-swap line shows a
    structural anomaly we know swaps create when sentence extraction
    or rewrite punctuation goes wrong. Used to back out unsafe swaps
    without trusting the LLM's punctuation."""
    for pat in _SWAP_BREAKAGE_PATTERNS:
        if pat in line:
            # Allow legitimate ellipses (`...`) and code/example blocks.
            if pat == ".." and "..." in line and ".." not in line.replace("...", ""):
                continue
            return f"introduced_{pat.strip() or 'whitespace'!r}"
    return None


def _sentence_count(text: str) -> int:
    """Cheap sentence count using terminator-followed-by-whitespace.
    Same boundary rule the overstatement gate uses, so `.git` and
    file extensions don't inflate the count."""
    return len(_SENT_COUNT_RE.findall(text)) or (1 if text.strip() else 0)


def _apply_overstatement_swaps(body: str,
                               candidates: list[dict[str, Any]]
                               ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """For each Gate A candidate that the LLM flagged `overstated` with a
    drop-in `suggested_rewrite`, substring-swap the original sentence in
    the body. Sentences that don't appear verbatim or appear more than
    once are queued for human review instead of risking ambiguous edits.

    Defense in depth: after the swap, we re-inspect the affected line
    for structural anomalies (doubled periods, dangling backticks, etc.)
    that earlier pipeline runs revealed are common when sentence
    extraction misjudges a boundary. Any swap that introduces breakage
    is reverted and queued.
    """
    applied: list[dict[str, Any]] = []
    queued: list[dict[str, Any]] = []
    new_body = body
    for c in candidates:
        verdict = c.get("verdict") or {}
        if verdict.get("verdict") != "overstated":
            continue
        rewrite = verdict.get("suggested_rewrite")
        sentence = c.get("sentence")
        if not rewrite or not sentence:
            queued.append({**c, "queue_reason": "missing_rewrite_or_sentence"})
            continue
        count = new_body.count(sentence)
        if count == 0:
            queued.append({**c, "queue_reason": "sentence_not_in_body"})
            continue
        if count > 1:
            queued.append({**c, "queue_reason": f"sentence_ambiguous_{count}_matches"})
            continue
        # LLM contract: the rewrite is a 1:1 replacement of `sentence`.
        # If it expands to multiple sentences, it's smuggling adjacent
        # text along (we've seen the LLM bolt the previous sentence on
        # as a prefix), and the swap will duplicate text in the body.
        if _sentence_count(rewrite) > _sentence_count(sentence):
            queued.append({**c, "queue_reason":
                           f"rewrite_sentence_count_grew:"
                           f"{_sentence_count(sentence)}->{_sentence_count(rewrite)}"})
            continue
        candidate_body = new_body.replace(sentence, rewrite, 1)
        # Locate the affected line in candidate_body and check it for
        # known breakage signatures introduced by sentence-boundary
        # mismatches. The raw_line baseline (before swap) is the same
        # line in the original body; if breakage exists in the new line
        # but not in the old, the swap is unsafe.
        affected_lines_new = [ln for ln in candidate_body.splitlines()
                              if rewrite.strip() and rewrite.split(".", 1)[0][:40] in ln]
        breakage = next((b for ln in affected_lines_new
                         if (b := _swap_introduced_breakage(ln))), None)
        if breakage:
            queued.append({**c, "queue_reason": f"swap_breakage:{breakage}"})
            continue
        new_body = candidate_body
        applied.append({"line": c.get("line"), "trigger": c.get("trigger"),
                        "old": sentence, "new": rewrite})
    return new_body, applied, queued


def _delete_off_topic_paragraphs(body: str,
                                 findings: list[dict[str, Any]]
                                 ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """For each Gate D finding with `off_topic` + suggested_action=delete,
    locate the paragraph by its `excerpt` (the LLM emits a ~200-char
    prefix of the offending paragraph) and remove the whole paragraph.

    A paragraph is the maximal block of non-empty lines bounded by blank
    lines. We never delete inside a fenced code block; the coherence
    auditor itself skips those, but we double-check.
    """
    applied: list[dict[str, Any]] = []
    queued: list[dict[str, Any]] = []
    for f in findings:
        if f.get("verdict") != "off_topic":
            continue
        action = (f.get("suggested_action") or "").strip()
        if not action.startswith("delete"):
            queued.append({**f, "queue_reason": f"action_not_delete:{action or 'null'}"})
            continue
        excerpt = (f.get("excerpt") or "").strip().rstrip("…").rstrip()
        if not excerpt:
            queued.append({**f, "queue_reason": "missing_excerpt"})
            continue
        # Collapse internal whitespace in excerpt for tolerant matching;
        # the LLM may have normalized line wraps.
        anchor_words = excerpt.split()[:6]
        if not anchor_words:
            queued.append({**f, "queue_reason": "empty_excerpt"})
            continue
        anchor = " ".join(anchor_words)

        paragraphs = _split_paragraphs(body)
        match_indices = [i for i, p in enumerate(paragraphs)
                         if anchor in " ".join(p["text"].split())]
        if len(match_indices) != 1:
            queued.append({**f, "queue_reason":
                           f"paragraph_match_count:{len(match_indices)}"})
            continue
        idx = match_indices[0]
        para = paragraphs[idx]
        if para.get("kind") != "prose":
            queued.append({**f, "queue_reason": f"paragraph_kind:{para.get('kind')}"})
            continue
        body = _remove_paragraph(body, para)
        applied.append({"section": f.get("section"),
                        "excerpt": excerpt[:160],
                        "removed_lines": para["end_line"] - para["start_line"] + 1})
    return body, applied, queued


def _split_paragraphs(body: str) -> list[dict[str, Any]]:
    """Walk the body once and return paragraph records.

    Each paragraph is `{start_line, end_line, text, kind}` where kind is
    `prose` (eligible for delete) or `code|table|details|frontmatter`
    (skip). 1-indexed inclusive line numbers. Blank-line-bounded.
    """
    out: list[dict[str, Any]] = []
    in_code = False
    in_frontmatter = False
    in_details = False
    lines = body.splitlines()
    buf: list[str] = []
    buf_start = 0
    buf_kind = "prose"

    def flush():
        nonlocal buf, buf_start, buf_kind
        if buf:
            out.append({"start_line": buf_start,
                        "end_line": buf_start + len(buf) - 1,
                        "text": "\n".join(buf),
                        "kind": buf_kind})
        buf = []
        buf_kind = "prose"

    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            buf_start = i + 1
            buf.append(line)
            buf_kind = "frontmatter"
            continue
        if in_frontmatter:
            buf.append(line)
            if line.strip() == "---":
                in_frontmatter = False
                flush()
            continue
        if line.startswith("```"):
            if not in_code:
                flush()
                buf_start = i + 1
                buf.append(line)
                buf_kind = "code"
                in_code = True
            else:
                buf.append(line)
                in_code = False
                flush()
            continue
        if in_code:
            buf.append(line)
            continue
        if line.lstrip().startswith("<details"):
            flush()
            in_details = True
            buf_start = i + 1
            buf.append(line)
            buf_kind = "details"
            continue
        if in_details:
            buf.append(line)
            if "</details>" in line.lower():
                in_details = False
                flush()
            continue
        if line.lstrip().startswith("|"):
            if buf_kind != "table":
                flush()
                buf_start = i + 1
                buf_kind = "table"
            buf.append(line)
            continue
        if not line.strip():
            flush()
            continue
        # Heading lines flush — they aren't paragraphs themselves.
        if line.startswith("#"):
            flush()
            continue
        if not buf:
            buf_start = i + 1
            buf_kind = "prose"
        buf.append(line)
    flush()
    return out


def _remove_paragraph(body: str, paragraph: dict[str, Any]) -> str:
    """Drop a paragraph (1-indexed inclusive) and one trailing blank line
    if the surrounding lines would otherwise collapse two blanks together.
    """
    lines = body.splitlines(keepends=True)
    start = paragraph["start_line"] - 1
    end = paragraph["end_line"]  # exclusive in slice
    # Also consume one trailing blank line if the next line is blank — we
    # don't want to leave double blank lines behind.
    if end < len(lines) and lines[end].strip() == "":
        end += 1
    elif start > 0 and lines[start - 1].strip() == "" and end < len(lines) \
            and lines[end - 1 if end <= start else end].strip() == "":
        # Conservative: keep surrounding spacing as-is.
        pass
    return "".join(lines[:start] + lines[end:])


# ---- orchestration --------------------------------------------------------


def run_pipeline(module_key: str, *, skip_research: bool = False,
                 auto_apply: bool = True,
                 gate_agent_text: str = "codex",
                 gate_agent_coherence: str = "gemini",
                 section_pool_ref: str | None = None) -> dict[str, Any]:
    module_path = resolve_module_path(module_key)
    normalized_key = module_path.relative_to(DOCS_ROOT).with_suffix("").as_posix()
    flat_key = normalized_key.replace("/", "-")
    run_record: dict[str, Any] = {
        "module_key": normalized_key,
        "module_path": str(module_path.relative_to(REPO_ROOT)),
        "started_at": _iso_utc(),
        "stages": {},
        "auto_apply": {"overstatement": {"applied": [], "queued": []},
                       "off_topic_delete": {"applied": [], "queued": []}},
        "queued_findings": {},
    }

    # Stage 1: research ----------------------------------------------------
    if skip_research:
        run_record["stages"]["research"] = {"skipped": True}
    else:
        r = run_research(
            normalized_key,
            agent="codex",
            section_pool_ref=section_pool_ref,
        )
        run_record["stages"]["research"] = r
        if not r.get("ok"):
            return _finalize(run_record, "research_failed", flat_key)
        if r.get("schema_issues"):
            pruned = _prune_schema_failed_claims(normalized_key, r.get("schema_issues") or [])
            run_record["stages"]["research_schema_prune"] = pruned
            if pruned.get("remaining_claims", 0) == 0 and not pruned.get("has_further_reading"):
                return _finalize(run_record, "research_schema_issues", flat_key)

    # Stage 2: verify (Gate B) ---------------------------------------------
    v = run_verify(normalized_key, agent="gemini")
    run_record["stages"]["verify"] = v
    if not v.get("ok"):
        return _finalize(run_record, "verify_failed", flat_key)
    if v.get("failing_count", 0) > 0:
        pruned = _prune_failed_cited_claims(normalized_key, v.get("verdict_path"))
        run_record["stages"]["verify_prune"] = pruned
        if pruned.get("remaining_citable", 0) == 0 and not pruned.get("has_further_reading"):
            return _finalize(run_record, "verify_unsupported_or_contradicted", flat_key)

    # Stage 3: inject in place --------------------------------------------
    inj = run_inject(normalized_key, agent="codex")
    run_record["stages"]["inject"] = inj
    if not inj.get("ok"):
        fb = _sources_only_fallback(normalized_key, module_path, inj)
        run_record["stages"]["inject_fallback"] = fb
        if not fb.get("ok"):
            return _finalize(run_record, "inject_failed", flat_key)

    # Stage 4: audit -------------------------------------------------------
    audit = _audit_all(module_path, gate_agent_text=gate_agent_text,
                       gate_agent_coherence=gate_agent_coherence)
    run_record["stages"]["audit_initial"] = _audit_summary(audit)

    if not auto_apply:
        run_record["queued_findings"] = _collect_residuals(audit)
        return _finalize(run_record, _final_status(audit), flat_key)

    # Stage 5: auto-apply --------------------------------------------------
    body = module_path.read_text(encoding="utf-8")
    body, a_applied, a_queued = _apply_overstatement_swaps(
        body, audit["A_overstatement"].get("candidates") or [])
    body, d_applied, d_queued = _delete_off_topic_paragraphs(
        body, audit["D_coherence"].get("findings") or [])
    if a_applied or d_applied:
        module_path.write_text(body, encoding="utf-8")
    run_record["auto_apply"]["overstatement"]["applied"] = a_applied
    run_record["auto_apply"]["overstatement"]["queued"] = a_queued
    run_record["auto_apply"]["off_topic_delete"]["applied"] = d_applied
    run_record["auto_apply"]["off_topic_delete"]["queued"] = d_queued

    # Stage 6: re-audit ----------------------------------------------------
    final_audit = audit
    if a_applied or d_applied:
        final_audit = _audit_all(module_path, gate_agent_text=gate_agent_text,
                                 gate_agent_coherence=gate_agent_coherence)
        run_record["stages"]["audit_final"] = _audit_summary(final_audit)
    else:
        run_record["stages"]["audit_final"] = run_record["stages"]["audit_initial"]
    residuals = _collect_residuals(final_audit)

    # Always queue Gate C needs_citation and Gate D rewrite_to_fit, plus
    # any A/D auto-apply queued items that didn't take.
    residuals.setdefault("overstatement_queued", []).extend(a_queued)
    residuals.setdefault("off_topic_delete_queued", []).extend(d_queued)
    run_record["queued_findings"] = residuals

    return _finalize(run_record, _final_status(final_audit), flat_key)


def _audit_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "A_overstatement": {
            "candidate_count": audit["A_overstatement"].get("candidate_count", 0),
            "overstated": sum(1 for c in audit["A_overstatement"].get("candidates") or []
                              if (c.get("verdict") or {}).get("verdict") == "overstated"),
        },
        "C_unsourced": {
            "candidate_count": audit["C_unsourced"].get("candidate_count", 0),
            "needs_citation": sum(1 for c in audit["C_unsourced"].get("candidates") or []
                                  if (c.get("verdict") or {}).get("verdict") == "needs_citation"),
        },
        "D_coherence": {
            "flag_count": audit["D_coherence"].get("flag_count", 0),
            "off_topic": sum(1 for f in audit["D_coherence"].get("findings") or []
                             if f.get("verdict") == "off_topic"),
        },
    }


def _collect_residuals(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "overstated_unfixed": [
            {"line": c.get("line"), "trigger": c.get("trigger"),
             "sentence": c.get("sentence"),
             "suggested_rewrite": (c.get("verdict") or {}).get("suggested_rewrite")}
            for c in audit["A_overstatement"].get("candidates") or []
            if (c.get("verdict") or {}).get("verdict") == "overstated"
        ],
        "needs_citation": [
            {"line": c.get("line"), "signals": c.get("signals"),
             "excerpt": c.get("excerpt"),
             "search_hint": (c.get("verdict") or {}).get("search_hint")}
            for c in audit["C_unsourced"].get("candidates") or []
            if (c.get("verdict") or {}).get("verdict") == "needs_citation"
        ],
        "off_topic_unfixed": [
            {"section": f.get("section"), "excerpt": f.get("excerpt"),
             "reason": f.get("reason"),
             "suggested_action": f.get("suggested_action")}
            for f in audit["D_coherence"].get("findings") or []
            if f.get("verdict") == "off_topic"
        ],
    }


def _final_status(audit: dict[str, Any]) -> str:
    return "clean" if _audit_is_clean(audit) else "residuals_queued"


def _finalize(run_record: dict[str, Any], status: str, flat_key: str) -> dict[str, Any]:
    run_record["status"] = status
    run_record["finished_at"] = _iso_utc()

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_path = RUNS_DIR / f"{flat_key}.json"
    run_path.write_text(json.dumps(run_record, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    run_record["_run_record_path"] = str(run_path.relative_to(REPO_ROOT))

    queued = run_record.get("queued_findings") or {}
    if any(queued.values()):
        HUMAN_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
        hr_path = HUMAN_REVIEW_DIR / f"{flat_key}.json"
        hr_path.write_text(json.dumps({
            "module_key": run_record["module_key"],
            "status": status,
            "queued_findings": queued,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        run_record["_human_review_path"] = str(hr_path.relative_to(REPO_ROOT))

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary_line = {
        "ts": run_record["finished_at"],
        "module_key": run_record["module_key"],
        "status": status,
        "audit_initial": (run_record["stages"].get("audit_initial") or {}),
        "audit_final": (run_record["stages"].get("audit_final") or {}),
        "overstatement_applied": len(
            run_record["auto_apply"]["overstatement"]["applied"]),
        "off_topic_deleted": len(
            run_record["auto_apply"]["off_topic_delete"]["applied"]),
        "queued_total": sum(len(v) for v in (run_record.get("queued_findings") or {}).values()),
    }
    with SUMMARY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(summary_line, ensure_ascii=False) + "\n")
    return run_record


# ---- CLI ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pipeline v3 — full content gate orchestrator")
    p.add_argument("module_key")
    p.add_argument("--skip-research", action="store_true",
                   help="reuse the existing seed (skip research dispatch)")
    p.add_argument("--no-auto-apply", action="store_true",
                   help="audit only; queue everything")
    p.add_argument("--gate-agent", default="codex", choices=["codex", "gemini"],
                   help="LLM for Gates A and C (default: codex)")
    p.add_argument("--coherence-agent", default="gemini", choices=["codex", "gemini"],
                   help="LLM for Gate D (default: gemini)")
    args = p.parse_args(argv)

    record = run_pipeline(
        args.module_key,
        skip_research=args.skip_research,
        auto_apply=not args.no_auto_apply,
        gate_agent_text=args.gate_agent,
        gate_agent_coherence=args.coherence_agent,
    )
    # Compact summary to stdout — full record is on disk.
    print(json.dumps({
        "module_key": record["module_key"],
        "status": record["status"],
        "audit_initial": record["stages"].get("audit_initial"),
        "audit_final": record["stages"].get("audit_final"),
        "overstatement_applied": len(
            record["auto_apply"]["overstatement"]["applied"]),
        "off_topic_deleted": len(
            record["auto_apply"]["off_topic_delete"]["applied"]),
        "queued_total": sum(len(v) for v in (record.get("queued_findings") or {}).values()),
        "run_record_path": record.get("_run_record_path"),
        "human_review_path": record.get("_human_review_path"),
    }, indent=2, ensure_ascii=False))
    return 0 if record.get("status") == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
