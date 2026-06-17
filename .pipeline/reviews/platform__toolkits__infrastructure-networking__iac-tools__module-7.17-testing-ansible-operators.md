## 2026-06-17 — `REVIEW` — `APPROVE`
**Reviewer:** opus-inline cross-family R2 (Anthropic ≠ codex/OpenAI fix author; ≠ cursor/Kimi R1) + independent upstream web-verification before the fix. **#1996, PR (Ansible-arc fix-pass).** Fix author: codex gpt-5.5 (`9c634bdb8`).
Cursor R1 flagged this module NEEDS CHANGES because its Molecule/Kuttl test contract did not match how the SDK actually injects CR spec, and the Kuttl asserts used labels the 7.12 role never sets.
**Defects fixed (web-verified vs Operator-SDK information-flow doc + Module 7.12 canonical role):**
- The fabricated `_demoapp_` variable prefix removed from every Molecule converge/scenario. The SDK injects spec fields as **top-level snake_case vars** (`replicas`, `image`, `port`) plus the reserved `ansible_operator_meta.name`/`.namespace`; the converge playbooks now mirror those names exactly, with an `ansible_operator_meta:` mock for CR identity. Default image `nginx:1.27-alpine` matches 7.12.
- The false claim that "the `_demoapp_` prefix convention is not arbitrary — the SDK generates these exact variable names" was corrected to describe the real top-level-snake_case + `ansible_operator_meta` injection.
- Kuttl `TestAssert` selector labels aligned to what the 7.12 role actually sets: `app.kubernetes.io/name: demoapp` + `app.kubernetes.io/instance: kuttl-test-app` (the CR instance name). The CR object remains named `kuttl-test-app`.
**Ground-checks:** verifier **T0 PASS**, body_words **5735** (floor 5000); 0 residual fabricated tokens; no NEW fabricated API; frontmatter untouched; 14 reachable Sources; `Hypothetical scenario:` labels intact. Labs now internally consistent with the 7.12 role contract end-to-end.
**APPROVE.**
