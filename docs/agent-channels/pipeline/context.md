# Pipeline Channel

Discussion about the module quality pipeline: fact-ledger architecture,
integrity gate, structural review, writer prompts, evidence mapping.

## Current Architecture
- Phase-0: fact-ledger (gpt-5.3-codex-spark)
- Tier-1: deterministic integrity gate (YAML lint, version floor, evidence mapping as warnings)
- Structural review: Gemini Pro (7 checks: LAB COV QUIZ EXAM DEPTH WHY PRES)
- Writer: Gemini Pro with K8s lifecycle + verified claims in prompt

## Known Gaps
- Evidence mapping (forward + reverse) is warnings-only because fact-ledger is topic-based not content-aware
- K8s version regex matches non-K8s versions (containerd, NVIDIA toolkit)
- Phase2 fact-check harness has CLI arg length limit
