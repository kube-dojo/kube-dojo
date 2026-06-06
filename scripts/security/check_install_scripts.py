#!/usr/bin/env python3
"""Supply-chain DETECTION tripwire — issue #1812 (Miasma-class worm defense).

`.npmrc` sets `ignore-scripts=true`, so dependency lifecycle scripts do not run
on install. That is PREVENTION. This script is DETECTION: it scans the installed
dependency tree and FAILS if any package *outside the audited allow-list* declares
a `preinstall`, `install`, or `postinstall` script.

Why detection matters even with prevention on: `ignore-scripts` stops the hook
from *executing*, but a freshly-compromised dependency can still *introduce* a
malicious hook into our tree (the Miasma worm republishes packages with forged
provenance). This tripwire surfaces that change so a human reviews it — instead of
it sitting silent until someone runs `npm install` on a machine without the guard.

Allow-list = the only two deps that legitimately need native install scripts:
  - esbuild : links the correct platform binary (postinstall)
  - sharp   : fetches the libvips native binary (install)
Adding to ALLOWLIST is a security decision and must be reviewed in its own commit.

Exit 0 = clean. Exit 1 = unreviewed install hook(s) found (or node_modules missing).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Deps permitted to run native install scripts. Keep this minimal and reviewed.
ALLOWLIST: set[str] = {"esbuild", "sharp"}

LIFECYCLE_HOOKS = ("preinstall", "install", "postinstall")

REPO_ROOT = Path(__file__).resolve().parents[2]
NODE_MODULES = REPO_ROOT / "node_modules"


def scan() -> dict[str, dict[str, str]]:
    """Return {package_name: {hook: command}} for every dep declaring a hook."""
    found: dict[str, dict[str, str]] = {}
    for pkg_json in NODE_MODULES.rglob("package.json"):
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        name = data.get("name")
        scripts = data.get("scripts") or {}
        if not name or not isinstance(scripts, dict):
            continue
        hooks = {h: scripts[h] for h in LIFECYCLE_HOOKS if h in scripts}
        if hooks:
            # last writer wins; we only need to know the hook exists
            found.setdefault(name, {}).update(hooks)
    return found


def main() -> int:
    if not NODE_MODULES.is_dir():
        print("ERROR: node_modules/ not found — run `npm ci` first.", file=sys.stderr)
        return 1

    found = scan()
    violations = {n: h for n, h in found.items() if n not in ALLOWLIST}
    allowed = {n: h for n, h in found.items() if n in ALLOWLIST}

    print(f"Scanned node_modules — {len(found)} package(s) declare install hooks.")
    if allowed:
        print(f"  Allow-listed (reviewed): {', '.join(sorted(allowed))}")

    if violations:
        print(
            f"\n  SUPPLY-CHAIN TRIPWIRE: {len(violations)} unreviewed install hook(s) found:",
            file=sys.stderr,
        )
        for name in sorted(violations):
            for hook, cmd in violations[name].items():
                print(f"    {name}  [{hook}]: {cmd[:120]}", file=sys.stderr)
        print(
            "\n  A dependency introduced a lifecycle script not on the audited "
            "allow-list.\n  This is how Miasma-class worms execute. Review the "
            "package and the diff before\n  proceeding. If legitimate, add it to "
            "ALLOWLIST in this file in a reviewed commit.",
            file=sys.stderr,
        )
        return 1

    print("OK — no unreviewed dependency install hooks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
