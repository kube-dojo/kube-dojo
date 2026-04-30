#!/usr/bin/env python3
"""HTTP-verify every URL in module ``## Sources`` sections.

Phase 0 of the ML curriculum expansion (issue #677) ships hard rails on
source-grounding. This script is one of two: it verifies that every URL
cited in the ``## Sources`` section of one or more markdown files
resolves to a 200 response on the same host (no cross-domain redirects,
no 404s, no soft-redirect-to-homepage).

Why "same host" matters: a frequent silent-stale failure mode is a
docs URL that 301s to a homepage when the original page disappears. The
HTTP status is 200 but the content is wrong. Hard-failing on
cross-host redirects catches that.

The script is intentionally stdlib + ``requests`` only — no new
dependencies — and is safe to run in CI or as a pre-commit hook.

Usage::

    .venv/bin/python scripts/quality/check_citations.py path/to/module.md
    .venv/bin/python scripts/quality/check_citations.py --all-ml
    .venv/bin/python scripts/quality/check_citations.py --json path/to/module.md
"""
from __future__ import annotations

import sys
from pathlib import Path

# Running this file directly adds its own directory to sys.path[0],
# which shadows the stdlib `queue` module with the sibling
# `scripts/quality/queue.py`. Drop the script's own directory before
# importing third-party modules. Module form (`python -m scripts.quality
# .check_citations`) sidesteps this entirely.
_HERE = str(Path(__file__).resolve().parent)
sys.path = [p for p in sys.path if p not in ("", _HERE)]

import argparse  # noqa: E402  (must follow sys.path adjustment)
import json  # noqa: E402
import re  # noqa: E402
from dataclasses import asdict, dataclass  # noqa: E402
from typing import Iterable  # noqa: E402
from urllib.parse import urlparse  # noqa: E402

import requests  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_DIRS = [
    REPO_ROOT / "src/content/docs/ai-ml-engineering/machine-learning",
    REPO_ROOT / "src/content/docs/ai-ml-engineering/reinforcement-learning",
]

USER_AGENT = "Mozilla/5.0 KubeDojo-citation-check"
REQUEST_TIMEOUT = 20  # seconds
MAX_REDIRECTS = 2

# Match URL inside markdown link [...](url) and bare http(s) URLs.
MD_LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)]+)\)")
BARE_URL_RE = re.compile(r"(?<![(\[])\bhttps?://[^\s)<>\]]+")


@dataclass
class CitationCheck:
    file: str
    url: str
    status: int | None
    final_url: str | None
    final_host: str | None
    original_host: str
    ok: bool
    error: str | None


def extract_sources_section(text: str) -> str | None:
    """Return the body of the ``## Sources`` section, or None.

    Greedily captures everything after ``## Sources`` until the next
    same-or-higher heading (``##`` or ``#``) or end of file.
    """
    match = re.search(
        r"^##\s+Sources\b.*?$(.*?)(?=^#{1,2}\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else None


def extract_urls(section_text: str) -> list[str]:
    """Return URLs in order of appearance, deduplicated, preserving order."""
    seen: dict[str, None] = {}
    for url in MD_LINK_RE.findall(section_text):
        seen.setdefault(url.rstrip(".,);'\""), None)
    for url in BARE_URL_RE.findall(section_text):
        # avoid double-counting URLs already captured inside markdown links
        cleaned = url.rstrip(".,);'\"")
        if cleaned not in seen:
            seen[cleaned] = None
    return list(seen)


def check_url(url: str) -> CitationCheck:
    original_host = urlparse(url).hostname or ""
    headers = {"User-Agent": USER_AGENT}
    session = requests.Session()
    session.max_redirects = MAX_REDIRECTS
    try:
        # Try HEAD first; some sites refuse HEAD with 405, fall back to GET.
        resp = session.head(
            url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True,
        )
        if resp.status_code in (405, 403, 501):
            resp = session.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=True,
            )
            resp.close()
    except requests.TooManyRedirects as exc:
        return CitationCheck(
            file="",
            url=url,
            status=None,
            final_url=None,
            final_host=None,
            original_host=original_host,
            ok=False,
            error=f"too many redirects: {exc}",
        )
    except requests.RequestException as exc:
        return CitationCheck(
            file="",
            url=url,
            status=None,
            final_url=None,
            final_host=None,
            original_host=original_host,
            ok=False,
            error=f"request failed: {exc}",
        )

    final_host = urlparse(resp.url).hostname or ""
    cross_host = (
        final_host != original_host
        and not final_host.endswith("." + original_host)
        and not original_host.endswith("." + final_host)
    )
    error: str | None = None
    if resp.status_code != 200:
        error = f"non-200 status: {resp.status_code}"
    elif cross_host:
        error = f"cross-host redirect: {original_host} -> {final_host}"

    return CitationCheck(
        file="",
        url=url,
        status=resp.status_code,
        final_url=resp.url,
        final_host=final_host,
        original_host=original_host,
        ok=error is None,
        error=error,
    )


def check_file(path: Path) -> list[CitationCheck]:
    text = path.read_text(encoding="utf-8")
    section = extract_sources_section(text)
    if section is None:
        return [
            CitationCheck(
                file=str(path),
                url="",
                status=None,
                final_url=None,
                final_host=None,
                original_host="",
                ok=False,
                error="no `## Sources` section found",
            )
        ]
    urls = extract_urls(section)
    if not urls:
        return []
    out: list[CitationCheck] = []
    for url in urls:
        result = check_url(url)
        result.file = str(path)
        out.append(result)
    return out


def iter_target_files(args: argparse.Namespace) -> Iterable[Path]:
    if args.all_ml:
        for d in ML_DIRS:
            if not d.exists():
                continue
            for p in sorted(d.rglob("*.md")):
                if p.name == "index.md":
                    continue
                yield p
        return
    for p in args.paths:
        path = Path(p).resolve()
        if not path.exists():
            print(f"warning: {path} does not exist", file=sys.stderr)
            continue
        yield path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="*", help="markdown files to check")
    parser.add_argument(
        "--all-ml",
        action="store_true",
        help="scan machine-learning/ + reinforcement-learning/ recursively",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="emit machine-readable JSON instead of a human table",
    )
    args = parser.parse_args(argv)

    if not args.paths and not args.all_ml:
        parser.error("provide one or more paths, or pass --all-ml")

    all_results: list[CitationCheck] = []
    for path in iter_target_files(args):
        all_results.extend(check_file(path))

    if args.json_output:
        json.dump(
            [asdict(r) for r in all_results],
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        if not all_results:
            print("no URLs found in any provided file's ## Sources section")
        else:
            print(f"{'STATUS':<10} {'HOST':<35} URL")
            print("-" * 100)
            for r in all_results:
                status = (
                    f"{r.status}"
                    if r.status is not None
                    else "ERR"
                )
                tag = "OK" if r.ok else "FAIL"
                print(f"{tag:<5}{status:<5} {r.final_host or r.original_host:<35} {r.url}")
                if r.error:
                    print(f"        - {r.error}")
                if r.file:
                    print(f"        ({r.file})")

    failures = [r for r in all_results if not r.ok]
    if failures:
        print(f"\n{len(failures)} citation(s) failed verification.", file=sys.stderr)
        return 1
    print(f"\nAll {len(all_results)} citation(s) verified.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
