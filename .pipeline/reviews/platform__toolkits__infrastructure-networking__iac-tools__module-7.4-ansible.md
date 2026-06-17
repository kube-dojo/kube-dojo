## 2026-06-17 — `REVIEW` — `APPROVE`
**Reviewer:** opus-inline cross-family R1 (Anthropic ≠ deepseek author; NO gemini) + web-verification (deepseek ground-checked hard per roster) + dead-link curl sweep. **#1996, PR (iac-stubs expand batch).** Author: deepseek-v4-pro.
Code-heavy stub (~203 prose words) expanded to T0 teaching prose.
**Ground-checks (web-verified — deepseek is fabrication-prone, so every checkable claim was verified):**
- **`ansible-core 2.21.0 (released 2026-05-18)` — VERIFIED REAL** (official ansible-core 2.21 roadmap scheduled 2026-05-18; forum release announcement; Arch package `2.21.0-1`). Correctly quarantined in a dated Landscape Snapshot.
- Red Hat acquired Ansible, Inc. **2015** ✓; license **GPL-3.0-or-later** ✓; `kubernetes.core` is the K8s collection ✓.
- Durable spine accurate: agentless/push/SSH-WinRM, **idempotency** as the core model, inventory→playbook→role→module hierarchy, Jinja2, handlers/notify, vault; `serial`/`max_fail_percentage` rolling-deploy semantics correct; inventory-cached-at-start behavior correct.
- **Ansible-vs-Terraform framed as complementary peers** ("The tools are peers with distinct strengths"), not a ranking — durable-content compliant. Cross-refs the Operator arc (7.12–7.17), AWX/EDA (7.14), Molecule (7.17) without duplicating.
- **War Story de-fabbed** → `## Hypothetical Scenario: The Patch That Could Have Broken Production` (no invented $/metrics). No fabricated stats found.
- Dead-link sweep: Sources clean (the curl-flagged `localhost`/`{{ }}` URLs are lab code, not sources).
**Verifier T0**, 12 sources, `revision_pending:false`, no anti-leak. **APPROVE.**
