"""KubeDojo Quality Pipeline v2 — module quality rewrite + citation verify-or-remove.

Package layout:

* :mod:`state`        — atomic state I/O + ``fcntl.flock`` leases
* :mod:`extractors`   — robust module-markdown + JSON extractors
* :mod:`worktree`     — git worktree lifecycle + primary-checkout resolver
* :mod:`dispatchers`  — Codex / Claude / Gemini wrappers with round-robin
* :mod:`prompts`      — prompt builders
* :mod:`citations`    — Lightpanda fetch + verify-or-remove (strict)
* :mod:`stages`       — audit / route / write / verify / review / merge
* :mod:`pipeline`     — orchestrator + subcommands

See ``docs/sessions/2026-04-24-quality-pipeline-redesign.md`` for the design
decisions behind this layout and the Codex must-fix list it closes.
"""
