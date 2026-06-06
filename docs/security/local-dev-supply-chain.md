# Local development — supply-chain hygiene

Developer guide for working safely with npm dependencies on KubeDojo ([issue #1812](https://github.com/kube-dojo/kube-dojo.github.io/issues/1812)).

## Lifecycle scripts are blocked

The repo root `.npmrc` sets:

```ini
ignore-scripts=true
```

`npm install` and `npm ci` **do not run** dependency `preinstall`, `install`, or `postinstall` hooks. That is intentional: a Miasma-class worm executes through those hooks to steal credentials and republish packages with forged provenance. Blocking scripts neutralises the attack locally, not only in CI.

### Building the site locally

Two audited native dependencies still need their install scripts after a fresh install:

- **esbuild** — `postinstall` links the platform binary
- **sharp** — `install` fetches the libvips native binary

Plain `npm rebuild` honours `ignore-scripts=true` and is a **no-op**. Re-enable scripts only for those packages:

```bash
npm ci
npm rebuild esbuild sharp --ignore-scripts=false
npm run build
```

CI's **Deploy to GitHub Pages** workflow runs the same rebuild step automatically.

## Token and credential hygiene

Miasma-class malware harvests **local npm tokens** and **GitHub credentials** from developer machines. Reduce exposure:

- Do **not** keep long-lived npm publish tokens on dev machines unless you are actively publishing.
- Prefer **short-lived**, **scoped** GitHub tokens (fine-grained PATs or `gh auth` session tokens) over broad legacy PATs.
- **Rotate** npm and GitHub tokens if you suspect exposure (suspicious lockfile diff, tripwire fire, or unexpected package publish).
- **Never** commit real tokens — examples in this repo use placeholders only (`changeme`, `example.com`).

## If a tripwire fires locally

Run the same deterministic checks CI uses:

```bash
python3 scripts/security/check_install_scripts.py
python3 scripts/security/check_lockfile_integrity.py
```

Then:

1. Read the output — each line is tagged (`[install-hook]`, `[lockfile-swap]`, etc.).
2. Open [detection-runbook.md](./detection-runbook.md) for the matching control and triage steps.
3. Inspect `git diff package-lock.json package.json` before committing.
4. For a **legitimate lockfile-only** change (e.g. `npm audit fix`), review carefully; CI accepts it only with the `[lockfile-only]` acknowledgement marker in the commit message (see runbook — not a security gate, only a review signal).

## Further reading

- [detection-runbook.md](./detection-runbook.md) — what each control does and how to respond
- [SECURITY.md](../../SECURITY.md) — reporting vulnerabilities
