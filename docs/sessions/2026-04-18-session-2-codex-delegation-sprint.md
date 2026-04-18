# Session Handoff — 2026-04-18 Session 2 — Codex Delegation Sprint

## Cold start (next session, read first)

```bash
scripts/services-up                                          # idempotent; brings up API + 3 pipeline workers
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1 # canonical orientation, ~0.7K tokens
gh pr list --repo kube-dojo/kube-dojo.github.io --author @me # 21 open PRs from this session need merge decisions
```

Everything else (pipeline state, service PIDs, flapping count, alerts) comes from the briefing. Don't `cat STATUS.md` first — it's fallback for when the API is down.

## Novel info (not derivable from briefing / git / PR list)

- **`scripts/ab` now defaults `CODEX_BRIDGE_MODE=workspace-write`** (this commit). Prior default `safe` silently blocked writes, worktrees, and `gh` — burned 15 min of session 2. For network + full FS access on risky tasks, override: `CODEX_BRIDGE_MODE=danger scripts/ab ask-codex ...`.
- **`scripts/services-up`** is idempotent. Run at start of every session — it skips already-running services and ages `.pids/*.pid` files to beat the local_api stale-PID heuristic (which is over-eager; TODO: fix that heuristic in `local_api.py` L2167-2180 so this hack isn't load-bearing).
- **Role-swap convention in practice**: Codex writes + opens PR; Claude posts adversarial review as a PR comment (not `gh pr review --approve` — fails because same GH identity owns both author and reviewer). LGTM signal is explicit in the comment body.
- **#279 timed out at 900s** — partial +655 LOC work in `.worktrees/citation-pipeline` uncommitted. Don't merge as-is. Split plan posted on #279: three sub-tasks (#279a seed injection, #279b citation gate step, #279c rubric dimension + e2e test), each ≤150 LOC.
- **Worktree builds fail** on Astro's `node_modules` symlink resolution (`Could not resolve "../../node_modules/@astrojs/starlight/style/layers.css"`). Always `npm run build` from primary `main` checkout, not a worktree. Bit PR #282; PR #299 got it right.

## PR stack — non-obvious merge dependencies

The briefing + `gh pr list` gives you the 21 PRs. These compositions aren't obvious from their titles:

- **#283 before #286** — stacked (PR 1b imports the constant PR 1a defines).
- **#290 before #291 and #296** — consecutive `check_failures` semantics must land before the transitions that assume it.
- **#288 before #294** — `needs_independent_review` flag revival must precede the fallback-chain change that sets it.
- **#287 + #289 before #302** — ledger purity + windowing must precede the "don't poison retries on REJECT" fix.
- **#282 needs re-verify from main** — ruff path + build path failed in worktree. Not a code issue.

Everything else merges cleanly in any order.

## Incomplete / for next session

- **Split + re-delegate #279** using the comment's plan. `CODEX_BRIDGE_MODE=danger scripts/ab ask-codex --task-id infra-279a ...` (danger because the citation pipeline touches many files and needs network for `gh`).
- **`TestStatusFourStage` pre-existing flake** — called out in 10+ review comments. Order-dependent; passes in isolation. Worth a dedicated cleanup PR.
- **#235 MEDIUM bugs remaining** — #302 closed the first. Others listed in the #235 body.
- **local_api stale-PID heuristic** (`scripts/local_api.py` L2167-2180) — replace `proc_age > pid_file_age + slack` check with a liveness check (`os.kill(pid, 0)`) + optional age threshold. Would retire the `touch -t` ritual in `scripts/services-up`.
