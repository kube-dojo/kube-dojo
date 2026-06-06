#!/usr/bin/env python3
"""Supply-chain DETECTION tripwire — issue #1812 (Miasma-class worm defense).

`.npmrc` sets `ignore-scripts=true` (PREVENTION: dependency lifecycle scripts do
not execute on install). This is DETECTION: it scans the dependency tree and FAILS
if a dependency can run install-time code that has not been explicitly audited —
so a freshly-introduced hook (the Miasma worm republishes packages with forged
provenance) is surfaced for human review instead of sitting silent until someone
runs `npm install` on a machine without the guard.

Authoritative source = `package-lock.json`, NOT the installed `node_modules`:
  - The lockfile lists EVERY dependency, including OS-gated optional ones that are
    not installed on this machine (e.g. `fsevents` on Linux) — node_modules misses
    those (cross-family review, codex/deepseek).
  - npm's `hasInstallScript` flag is TRUE for preinstall/install/postinstall AND
    for implicit node-gyp builds (`binding.gyp` with no declared script) — reading
    `package.json.scripts` alone misses the latter (e.g. `fsevents`).
  - The lockfile PATH (`node_modules/<name>`) is the resolved identity, so a
    package that lies about its `name` in package.json cannot spoof the allow-list,
    and a package with a null/empty name cannot evade the scan (review: all three).

Three gates (any violation => exit 1):
  1. INSTALL HOOKS: every `hasInstallScript` package must be in ALLOWLIST_INSTALL.
  2. ALLOW-LIST ABUSE: an allow-listed package's *declared* install hooks must be a
     subset of EXPECTED_HOOKS — so a compromised esbuild/sharp that adds a rogue
     preinstall is still caught.
  3. NON-REGISTRY SOURCE: any dep resolved from git/local/tarball is flagged — those
     bypass registry signing and DO run `prepare` on install (the `prepare` surface
     that npm's `hasInstallScript` does not cover; registry deps do not run `prepare`
     on `npm ci`).

Adding to any allow-list is a security decision — review it in its own commit.

Exit 0 = clean. Exit 1 = unaudited install-time code found (or lockfile missing).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Packages permitted to carry an install script (lockfile `hasInstallScript`).
# Keep minimal and reviewed. Identity is the lockfile path, not the declared name.
ALLOWLIST_INSTALL: set[str] = {"esbuild", "fsevents", "sharp"}

# For an allow-listed package, its DECLARED install-lifecycle hooks must be a subset
# of these. fsevents builds via binding.gyp with no explicit script => empty set.
EXPECTED_HOOKS: dict[str, set[str]] = {
    "esbuild": {"postinstall"},
    "sharp": {"install"},
    "fsevents": set(),
}

INSTALL_LIFECYCLE = ("preinstall", "install", "postinstall")
REGISTRY_PREFIX = "https://registry.npmjs.org/"

REPO_ROOT = Path(__file__).resolve().parents[2]


def name_from_lock_path(path: str) -> str:
    """Resolved package identity = the segment after the last `node_modules/`.
    Handles scopes: `node_modules/@astrojs/starlight` -> `@astrojs/starlight`."""
    return path.split("node_modules/")[-1]


def declared_install_hooks(node_modules: Path, name: str) -> set[str] | None:
    """Read the installed package's declared install hooks. None if not installed."""
    pkg_json = node_modules / Path(*name.split("/")) / "package.json"
    if not pkg_json.is_file():
        return None
    try:
        scripts = json.loads(pkg_json.read_text(encoding="utf-8")).get("scripts") or {}
    except (ValueError, OSError):
        return set()
    if not isinstance(scripts, dict):
        return set()
    return {h for h in INSTALL_LIFECYCLE if h in scripts}


def main(argv: list[str]) -> int:
    lockfile = Path(argv[1]) if len(argv) > 1 else REPO_ROOT / "package-lock.json"
    if not lockfile.is_file():
        print(f"ERROR: lockfile not found: {lockfile}", file=sys.stderr)
        return 1
    node_modules = lockfile.parent / "node_modules"

    try:
        packages = json.loads(lockfile.read_text(encoding="utf-8")).get("packages", {})
    except (ValueError, OSError) as exc:
        print(f"ERROR: cannot parse {lockfile}: {exc}", file=sys.stderr)
        return 1

    install_hook_pkgs: list[str] = []
    violations: list[str] = []

    for path, meta in packages.items():
        if not path or meta.get("link"):  # root package / workspace symlink
            continue
        name = name_from_lock_path(path)

        # Gate 1 + 2: install scripts
        if meta.get("hasInstallScript"):
            install_hook_pkgs.append(name)
            if name not in ALLOWLIST_INSTALL:
                violations.append(
                    f"[install-hook] {path} — declares an install script and is NOT "
                    f"on the audited allow-list {sorted(ALLOWLIST_INSTALL)}"
                )
            else:
                actual = declared_install_hooks(node_modules, name)
                expected = EXPECTED_HOOKS.get(name, set())
                if actual is not None and not actual <= expected:
                    violations.append(
                        f"[allow-list-abuse] {path} — allow-listed but declares "
                        f"unexpected hook(s) {sorted(actual - expected)} "
                        f"(expected ⊆ {sorted(expected) or '∅'})"
                    )

        # Gate 3: non-registry source (git/local/tarball — runs `prepare`, unsigned)
        resolved = meta.get("resolved") or ""
        if resolved and not resolved.startswith(REGISTRY_PREFIX):
            violations.append(
                f"[non-registry] {path} — resolved from a non-registry source "
                f"({resolved[:60]}); these run `prepare` on install and bypass "
                f"registry signing"
            )

    print(
        f"Scanned {lockfile.name}: {len(install_hook_pkgs)} package(s) with install "
        f"scripts ({', '.join(sorted(install_hook_pkgs)) or 'none'})."
    )

    if violations:
        print(
            f"\n  SUPPLY-CHAIN TRIPWIRE: {len(violations)} finding(s) — "
            f"unaudited install-time code:",
            file=sys.stderr,
        )
        for v in violations:
            print(f"    {v}", file=sys.stderr)
        print(
            "\n  This is how Miasma-class worms execute. Review the package(s) and "
            "the lockfile diff.\n  If legitimate, update ALLOWLIST_INSTALL / "
            "EXPECTED_HOOKS in this file in a reviewed commit.",
            file=sys.stderr,
        )
        return 1

    print("OK — no unaudited dependency install-time code.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
