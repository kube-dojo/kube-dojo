# Supply-chain detection runbook

Operational guide for Miasma-class npm/CI supply-chain defenses ([issue #1812](https://github.com/kube-dojo/kube-dojo.github.io/issues/1812)).

## Strategy

You cannot fully prevent being *reached* by a dependency attack. Failure conditions are a malicious hook **executing**, reaching a **secret**, **spreading** to other packages, or doing any of that **undetected**. Success means **zero blast radius** (hooks do not run, secrets are unreachable at install time) plus **fast time-to-detect** when the tree changes.

Layers: **PREVENT** (stop execution) → **DETECT** (surface changes) → **CONTAIN** (limit credential exposure) → **RESPOND** (triage below).

---

## Controls

### 1. `ignore-scripts=true` (`.npmrc`) — PREVENT

| | |
|---|---|
| **What** | Blocks all dependency lifecycle scripts (`preinstall` / `install` / `postinstall`) on `npm install` and `npm ci`. |
| **Attack signal** | N/A — primary control. A Miasma-class worm's execution point is an install hook; this neutralises it in CI and local dev. |
| **Where it surfaces** | Every `npm ci` / `npm install` (local + CI). Not a CI failure by itself. |
| **Time-to-detect** | Immediate at install time (hook does not run). |
| **Response** | No tripwire fire. After install, run `npm rebuild esbuild sharp --ignore-scripts=false` if you need a local build (see [local-dev-supply-chain.md](./local-dev-supply-chain.md)). |

---

### 2. Lifecycle-script tripwire (`scripts/security/check_install_scripts.py`) — DETECT

| | |
|---|---|
| **What** | Scans `package-lock.json` for unaudited install-time code: new `hasInstallScript` packages, allow-list abuse, non-registry `resolved` URLs, `file:`/local links, alias masquerade. |
| **Attack signal** | New or changed install hook; dependency resolved from git/tarball/local; compromised allow-listed package adding rogue hooks. |
| **Where it surfaces** | Workflow **Supply-chain detection** → job `detect` → step **Lifecycle-script tripwire**. CI failure (exit 1). |
| **Time-to-detect** | Next PR/push to `main` (minutes). |
| **Response** | 1. Read stderr lines (`[install-hook]`, `[non-registry]`, etc.). 2. Inspect lockfile diff and the flagged package on the registry. 3. If legitimate (e.g. new native dep), update `ALLOWLIST_INSTALL` / `EXPECTED_HOOKS` in the script in a **separate reviewed commit**. 4. If malicious, do not merge; rotate tokens (see local-dev doc); report via [SECURITY.md](../../SECURITY.md). |

---

### 3. Provenance / signature gate (`npm audit signatures`) — DETECT

| | |
|---|---|
| **What** | Verifies npm registry package attestations/signatures for locked dependencies. |
| **Attack signal** | Unsigned package, invalid signature, or forged provenance after a republish attack. |
| **Where it surfaces** | Workflow **Supply-chain detection** → job `detect` → step **Verify dependency provenance / signatures**. CI failure. May also appear in GitHub **Security** tab depending on org settings. |
| **Time-to-detect** | Next PR/push (minutes). |
| **Response** | 1. Identify which package failed from `npm audit signatures` output. 2. Compare lockfile `integrity` / `resolved` with the known-good registry artifact. 3. If supply-chain incident, block merge, rotate credentials, audit recent publishes. 4. If npm/registry outage or tooling bug, document and track separately — do not disable without review. |

---

### 4. Lockfile-integrity tripwire (`scripts/security/check_lockfile_integrity.py`) — DETECT

| | |
|---|---|
| **What** | Git-diff tripwire: any installer-affecting metadata change (version, resolved, integrity, bin, dependency edges, os/cpu, install-script flag, …) in `package-lock.json` **without** a matching `package.json` change in the same range. |
| **Attack signal** | Silent lockfile swap — attacker mutates the lockfile to point at a malicious tarball while leaving `package.json` unchanged; `npm ci` installs it blindly. |
| **Where it surfaces** | Workflow **Supply-chain detection** → job `detect` → step **Lockfile-integrity tripwire**. CI failure (exit 1) with `[lockfile-swap]` paths. |
| **Time-to-detect** | Next PR/push (minutes). |
| **Override** | Suppressed if HEAD commit message contains literal `[lockfile-only]` or env `LOCKFILE_OVERRIDE=1`. **This is an acknowledgement marker, not an authorization control** — an attacker could add the token; value is forcing human review of lockfile-only diffs (e.g. `npm audit fix`, transitive maintenance). |
| **Response** | 1. Review every listed package path and field diff. 2. Confirm the resolved URL and integrity match intended registry artifacts. 3. If legitimate lockfile-only maintenance, re-commit with `[lockfile-only]` in the message **after** review, or bump `package.json` in the same PR. 4. If unexplained, treat as incident — do not merge. |

---

### 5. Dependabot cooldown (7 days) — slow adoption

| | |
|---|---|
| **What** | `.github/dependabot.yml` sets `cooldown: { default-days: 7 }` on pip, github-actions, and npm ecosystems. |
| **Attack signal** | Tag-mutation / republish attacks where a poisoned version is published and quickly auto-merged. |
| **Where it surfaces** | Dependabot PRs delayed 7 days after a new tag. Not a CI failure. zizmor `dependabot-cooldown` audit in workflow **GitHub Actions security scan**. |
| **Time-to-detect** | Up to 7 days before auto-proposed bump (disclosure window for the community). |
| **Response** | When Dependabot opens a bump, normal review still applies; cooldown only delays adoption. Do not remove cooldown without security review. |

---

### 6. Build/deploy job separation (`deploy.yml`) — CONTAIN

| | |
|---|---|
| **What** | `build` job: `npm ci` + build with `contents: read` only — **no** OIDC/Pages token. `deploy` job: `id-token: write` + `pages: write`, **no** npm. |
| **Attack signal** | Compromised dependency executing during install and attempting to exfiltrate CI credentials. |
| **Where it surfaces** | Architectural — not a detector. Failure would be credential misuse in Actions logs or external exfil (if prevention failed). |
| **Time-to-detect** | N/A (prevents reach). |
| **Response** | Never co-locate `npm ci` with the privileged deploy job. If refactoring workflows, preserve this boundary. |

---

### 7. zizmor + SHA-pinned actions — PREVENT / DETECT (Actions layer)

| | |
|---|---|
| **What** | `zizmor` scans `.github/` for workflow vulnerabilities; all `uses:` actions are pinned to full commit SHAs. |
| **Attack signal** | Mutable action tags, excessive permissions, unpinned third-party actions, missing Dependabot cooldown, etc. |
| **Where it surfaces** | Workflow **GitHub Actions security scan** → job `zizmor`. CI failure on findings. |
| **Time-to-detect** | PR touching `.github/workflows/**`, `.github/actions/**`, or `.github/dependabot.yml`. |
| **Response** | Fix findings per zizmor output; run locally: `uvx zizmor --offline --strict-collection .github/`. |

---

### 8. harden-runner egress monitoring — PENDING

| | |
|---|---|
| **What** | StepSecurity **harden-runner** egress allow-listing and anomaly detection for GitHub Actions runners. |
| **Status** | **Not yet enabled** — requires installing the StepSecurity GitHub App at the **organisation** level (owner action; same class as issue #1798). |
| **Attack signal** | Unexpected outbound connections from CI (exfiltration, C2) if a hook or action is compromised. |
| **Where it surfaces** | Would appear in StepSecurity dashboard + optional CI annotations once enabled. |
| **Response** | Track as follow-up to #1812; enable org app when owner approves. |

---

### 9. Agent-config injection tripwire (`scripts/security/check_agent_configs.py`) — DETECT

| | |
|---|---|
| **What** | Whole-file regex scan of AI IDE agent-config paths (`.claude/**`, `.cursor/**`, `AGENTS.md`, `CLAUDE.md`, etc.) for high-signal auto-exec compositions — piped-to-shell downloaders, base64-to-shell, `eval` of command substitution, `child_process` exec, PowerShell `IEX`, Python remote-exec patterns. |
| **Attack signal** | Miasma agent-config-injection variant — auto-exec payload planted in agent config so it runs when the repo is opened in an AI IDE (e.g. `curl … \| bash`, or instructions to fetch and execute a remote payload). |
| **Where it surfaces** | Pre-commit hook **agent-config auto-exec injection scan** (local). Workflow **Supply-chain detection** → job `detect` → step **Agent-config injection tripwire**. CI failure (exit 1) with `[tag] path:line` lines. |
| **Time-to-detect** | Next commit locally (pre-commit) or PR/push to `main` (minutes). |
| **Override** | Suppressed if the flagged line or the line immediately above contains literal `agent-config-allow`. **This is an acknowledgement marker, not an authorization control** — anyone who can edit the file can add it; value is forcing human review of flagged auto-exec lines before they ship. |
| **Response** | 1. Read stderr (`[pipe-to-shell]`, `[eval-cmd-subst]`, etc.). 2. Inspect the flagged file and line — treat as incident unless you can explain it. 3. If malicious, do not merge; rotate tokens; report via [SECURITY.md](../../SECURITY.md). 4. If a legitimate documentation example reviewed by a human, add `agent-config-allow` on that line or the line above **after** review. |

---

## Quick triage checklist

When any **DETECT** control fires:

1. **Do not merge** until understood.
2. Run locally: `python3 scripts/security/check_install_scripts.py`, `python3 scripts/security/check_lockfile_integrity.py`, and `python3 scripts/security/check_agent_configs.py`.
3. Inspect `git diff` for `package-lock.json` and `package.json`.
4. Check registry pages for affected packages (version, publish date, maintainer).
5. If incident: rotate npm and GitHub tokens, audit recent publishes, file a security report.
6. Read [local-dev-supply-chain.md](./local-dev-supply-chain.md) for developer hygiene.
