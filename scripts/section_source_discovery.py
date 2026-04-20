#!/usr/bin/env python3
"""Discover a validated shared source pool for one curriculum section.

Usage:
    python scripts/section_source_discovery.py <section_path>
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
    DOCS_ROOT,
    REPO_ROOT,
    dispatch_codex,
    flat_section_name,
    parse_agent_response,
    section_pool_path_for,
)
from fetch_citation import allowlist_tier, fetch  # type: ignore  # noqa: E402


DEFAULT_BATCH_SIZE = 5
DEFAULT_MAX_BATCH_CHARS = 28_000
DEFAULT_MODULE_EXCERPT_CHARS = 6_000
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_URL_RE = re.compile(r"https?://[^\s)\"'`>]+")
_URL_SKIP_MARKERS = (
    "example.com",
    "example.org",
    "YOUR_ORG",
    "/org/",
    "localhost",
)
_TOOL_FALLBACKS = {
    "argocd": {
        "url": "https://argoproj.github.io/argo-cd/",
        "title": "Argo CD Documentation",
        "scope_notes": "Argo CD architecture, applications, sync policies, and operations.",
    },
    "argo rollouts": {
        "url": "https://argoproj.github.io/rollouts/",
        "title": "Argo Rollouts Documentation",
        "scope_notes": "Progressive delivery, canary releases, blue-green, and analysis runs.",
    },
    "flux": {
        "url": "https://fluxcd.io/flux/components/",
        "title": "Flux Components",
        "scope_notes": "Flux controller architecture, reconciliation, and GitOps toolkit resources.",
    },
    "helm": {
        "url": "https://helm.sh/docs/",
        "title": "Helm Documentation",
        "scope_notes": "Helm charts, templating, packaging, and release workflows.",
    },
    "kustomize": {
        "url": "https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/",
        "title": "Kustomize with kubectl",
        "scope_notes": "Kustomize bases, overlays, and patching without templates.",
    },
}


SECTION_DISCOVERY_PROMPT_TEMPLATE = """You are the section-level source discovery
step of the KubeDojo citation pipeline.

Your job: read the related modules below and return a JSON object with a
shared pool of PRIMARY sources that can support claims across this section.

Rules:
- Prefer shared, reusable primary sources over one-off marketing pages.
- Do NOT invent URLs. Use URLs you are confident exist.
- Pick sources that are broad enough to cover adjacent modules, but still
  concrete enough that later per-claim verification can succeed.
- Keep the pool small and high-signal: usually 4-10 sources per batch.
- Return only sources that belong to the trusted-domain allowlist tiers.
- `scope_notes` should say what kinds of claims the source can honestly back.
- `relevant_modules` should be a list of module keys from this batch.

Return ONE JSON object, no markdown fences, no prose:

{{
  "section": "{section}",
  "modules": ["module-key", "..."],
  "sources": [
    {{
      "url": "https://...",
      "title": "Short source title",
      "tier": "standards | upstream | vendor | incidents | general",
      "scope_notes": "What this source can back",
      "relevant_modules": ["module-key", "..."]
    }}
  ],
  "notes": "optional"
}}

Section: {section}
Modules in this batch:

{module_block}

Return the JSON now.
"""


def _iso_utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


def normalize_section_key(section_path: str) -> str:
    candidate = section_path.strip().strip("/")
    section_dir = DOCS_ROOT / candidate
    if not section_dir.exists() or not section_dir.is_dir():
        raise FileNotFoundError(f"section path not found: {section_path}")
    return section_dir.relative_to(DOCS_ROOT).as_posix()


def list_section_modules(section_path: str) -> list[Path]:
    section_key = normalize_section_key(section_path)
    section_dir = DOCS_ROOT / section_key
    return sorted(
        path for path in section_dir.glob("module-*.md")
        if path.is_file()
    )


def _module_excerpt(module_path: Path, *, max_chars: int = DEFAULT_MODULE_EXCERPT_CHARS) -> str:
    body = module_path.read_text(encoding="utf-8")
    if len(body) <= max_chars:
        return body
    return body[:max_chars].rstrip() + "\n\n[... truncated for section batch size ...]"


def _module_key(module_path: Path) -> str:
    return module_path.relative_to(DOCS_ROOT).with_suffix("").as_posix()


def batch_section_modules(
    module_paths: list[Path],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
) -> list[list[Path]]:
    batches: list[list[Path]] = []
    current: list[Path] = []
    current_chars = 0
    for module_path in module_paths:
        excerpt = _module_excerpt(module_path)
        excerpt_chars = len(excerpt)
        if current and (len(current) >= batch_size or current_chars + excerpt_chars > max_batch_chars):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(module_path)
        current_chars += excerpt_chars
    if current:
        batches.append(current)
    return batches


def build_section_discovery_prompt(section_key: str, module_paths: list[Path]) -> str:
    rendered_modules: list[str] = []
    for module_path in module_paths:
        module_key = _module_key(module_path)
        rendered_modules.append(
            f"## {module_key}\n\n```markdown\n{_module_excerpt(module_path)}\n```"
        )
    return SECTION_DISCOVERY_PROMPT_TEMPLATE.format(
        section=section_key,
        module_block="\n\n".join(rendered_modules),
    )


def _validate_discovered_sources(
    sources: list[dict[str, Any]],
    *,
    rejected_urls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for source in sources:
        url = str(source.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        tier = allowlist_tier(url)
        if tier is None:
            rejected_urls.append({
                "url": url,
                "reason": "off_allowlist",
                "at_step": "section_source_discovery",
            })
            continue
        result = fetch(url)
        status = int(result.get("status") or 0)
        issues = result.get("issues") or []
        if not (status and status < 400) or "pdf_needs_adapter" in issues:
            rejected_urls.append({
                "url": url,
                "reason": "pdf_no_adapter" if "pdf_needs_adapter" in issues else (
                    f"http_{status}" if status else "network_failure"
                ),
                "at_step": "section_source_discovery",
            })
            continue
        kept.append({
            "url": url,
            "title": str(source.get("title") or url).strip(),
            "tier": tier,
            "scope_notes": str(source.get("scope_notes") or "").strip(),
            "relevant_modules": sorted({
                str(module_key).strip()
                for module_key in (source.get("relevant_modules") or [])
                if str(module_key).strip()
            }),
        })
        seen_urls.add(url)
    return kept


def _merge_sources(batch_sources: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for sources in batch_sources:
        for source in sources:
            url = str(source.get("url") or "").strip()
            if not url:
                continue
            current = merged.setdefault(
                url,
                {
                    "url": url,
                    "title": str(source.get("title") or url).strip(),
                    "tier": str(source.get("tier") or "").strip(),
                    "scope_notes": str(source.get("scope_notes") or "").strip(),
                    "relevant_modules": [],
                },
            )
            if not current.get("scope_notes") and source.get("scope_notes"):
                current["scope_notes"] = str(source.get("scope_notes") or "").strip()
            current["relevant_modules"] = sorted({
                *current.get("relevant_modules", []),
                *(str(module_key).strip() for module_key in (source.get("relevant_modules") or [])),
            })
    final_sources: list[dict[str, Any]] = []
    for i, source in enumerate(merged.values(), start=1):
        final_sources.append({
            "source_id": f"S{i:03d}",
            "url": source["url"],
            "title": source["title"],
            "tier": source["tier"],
            "scope_notes": source["scope_notes"],
            "relevant_modules": source["relevant_modules"],
        })
    return final_sources


def _fallback_sources_from_modules(module_paths: list[Path]) -> list[dict[str, Any]]:
    discovered: dict[str, dict[str, Any]] = {}
    section_text = "\n".join(
        module_path.read_text(encoding="utf-8", errors="replace")
        for module_path in module_paths
    ).lower()

    for module_path in module_paths:
        module_key = _module_key(module_path)
        body = module_path.read_text(encoding="utf-8", errors="replace")
        for title, url in _LINK_RE.findall(body):
            if any(marker in url for marker in _URL_SKIP_MARKERS):
                continue
            if allowlist_tier(url) is None:
                continue
            current = discovered.setdefault(
                url,
                {
                    "url": url,
                    "title": title.strip() or url,
                    "tier": allowlist_tier(url),
                    "scope_notes": "Explicitly referenced in the section module body.",
                    "relevant_modules": [],
                },
            )
            current["relevant_modules"] = sorted({
                *current.get("relevant_modules", []),
                module_key,
            })

        for url in _URL_RE.findall(body):
            if any(marker in url for marker in _URL_SKIP_MARKERS):
                continue
            if allowlist_tier(url) is None:
                continue
            current = discovered.setdefault(
                url,
                {
                    "url": url,
                    "title": url,
                    "tier": allowlist_tier(url),
                    "scope_notes": "Explicit URL present in the section module body.",
                    "relevant_modules": [],
                },
            )
            current["relevant_modules"] = sorted({
                *current.get("relevant_modules", []),
                module_key,
            })

    for keyword, source in _TOOL_FALLBACKS.items():
        if keyword not in section_text:
            continue
        url = source["url"]
        current = discovered.setdefault(
            url,
            {
                "url": url,
                "title": source["title"],
                "tier": allowlist_tier(url),
                "scope_notes": source["scope_notes"],
                "relevant_modules": [_module_key(module_path) for module_path in module_paths],
            },
        )
        current["relevant_modules"] = sorted({
            *current.get("relevant_modules", []),
            *[_module_key(module_path) for module_path in module_paths],
        })

    ranked = sorted(
        discovered.values(),
        key=lambda source: (
            -len(source.get("relevant_modules") or []),
            len(source.get("url") or ""),
        ),
    )
    return ranked[:10]


def discover_section_sources(
    section_path: str,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_batch_chars: int = DEFAULT_MAX_BATCH_CHARS,
) -> dict[str, Any]:
    section_key = normalize_section_key(section_path)
    module_paths = list_section_modules(section_key)
    if not module_paths:
        return {"ok": False, "section": section_key, "error": "no_modules_found"}

    rejected_urls: list[dict[str, Any]] = []
    validated_batches: list[list[dict[str, Any]]] = []
    raw_batch_count = 0

    for batch in batch_section_modules(
        module_paths,
        batch_size=batch_size,
        max_batch_chars=max_batch_chars,
    ):
        raw_batch_count += 1
        prompt = build_section_discovery_prompt(section_key, batch)
        task_id = (
            f"section-source-discovery-{flat_section_name(section_key)}-"
            f"b{raw_batch_count}-{_dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')}"
        )
        ok, raw = dispatch_codex(prompt, task_id=task_id)
        if not ok:
            return {
                "ok": False,
                "section": section_key,
                "error": "dispatch_failed",
                "detail": raw[-600:],
            }
        try:
            parsed = parse_agent_response(raw)
        except (ValueError, json.JSONDecodeError) as exc:
            return {
                "ok": False,
                "section": section_key,
                "error": "parse_failed",
                "detail": str(exc),
            }
        if not isinstance(parsed, dict):
            return {
                "ok": False,
                "section": section_key,
                "error": "invalid_response_shape",
                "detail": f"expected object, got {type(parsed).__name__}",
            }
        sources = parsed.get("sources") or []
        if not isinstance(sources, list):
            return {
                "ok": False,
                "section": section_key,
                "error": "invalid_sources_shape",
            }
        validated_batches.append(
            _validate_discovered_sources(
                [source for source in sources if isinstance(source, dict)],
                rejected_urls=rejected_urls,
            )
        )

    merged_sources = _merge_sources(validated_batches)
    fallback_used = False
    if len(merged_sources) < 3:
        fallback_sources = _validate_discovered_sources(
            _fallback_sources_from_modules(module_paths),
            rejected_urls=rejected_urls,
        )
        if fallback_sources:
            merged_sources = _merge_sources([fallback_sources])
            fallback_used = True
    if len(merged_sources) < 3:
        return {
            "ok": False,
            "section": section_key,
            "error": "insufficient_validated_sources",
            "module_count": len(module_paths),
            "source_count": len(merged_sources),
            "rejected_count": len(rejected_urls),
            "fallback_used": fallback_used,
        }
    pool_path = section_pool_path_for(section_key)
    pool = {
        "section": section_key,
        "modules": [_module_key(module_path) for module_path in module_paths],
        "generated_at": _iso_utc_now(),
        "batch_count": raw_batch_count,
        "fallback_used": fallback_used,
        "sources": merged_sources,
        "rejected_urls": rejected_urls,
    }
    pool_path.write_text(json.dumps(pool, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "section": section_key,
        "module_count": len(module_paths),
        "batch_count": raw_batch_count,
        "source_count": len(merged_sources),
        "rejected_count": len(rejected_urls),
        "fallback_used": fallback_used,
        "pool_path": str(pool_path.relative_to(REPO_ROOT)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover a shared source pool for one section")
    parser.add_argument("section_path", help="Section path under src/content/docs/")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-batch-chars", type=int, default=DEFAULT_MAX_BATCH_CHARS)
    args = parser.parse_args(argv)

    result = discover_section_sources(
        args.section_path,
        batch_size=args.batch_size,
        max_batch_chars=args.max_batch_chars,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
