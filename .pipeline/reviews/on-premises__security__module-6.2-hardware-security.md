# Review Audit: on-premises/security/module-6.2-hardware-security

**Path**: `src/content/docs/on-premises/security/module-6.2-hardware-security.md`
**First pass**: 2026-04-14T10:17:12Z
**Last pass**: 2026-04-14T10:17:12Z
**Total passes**: 1
**Current phase**: review
**Current reviewer**: gemini
**Current severity**: None

---

## 2026-04-14T10:17:12Z — `WRITE`

**Writer**: gemini-3.1-pro-preview
**Mode**: write
**Plan**: Draft or improve the module at on-premises/security/module-6.2-hardware-security per the topic spec in the module frontmatter and any TODO comments in the existing stub.
**Output**: 26205 chars
**Duration**: 2m 34s

---

## 2026-06-11T13:48:50Z — `REVIEW` — `APPROVE`
On-premises security chapter (#1881, PR #1893). T3→T0 expand 1108→6527w (39 sources). Author: codex. Reviewer: deepseek (R1, cross-family) NEEDS_CHANGES → fixed. Every finding ground-checked vs the live file + web-verified. 1×P1: fabricated PKCS#11 v3.2 status/date ("Committee Specification, November 2025") → web-verified it is Committee Specification Draft 01, 16 Apr 2025; corrected to v3.1-current-OASIS-Standard with a dated v3.2-draft note. 2×P2: `kms-vault-provider` clarified as an example plugin name (not a standard binary); IEEE Spectrum source repointed from AMP URL to canonical (fixed the lone 301 → 0 redirects) + corrected its mismatched annotation (was "RSA naming", URL is QRNG → reframed to QRNG/hardware-entropy). Nits: PCR[0]-all-zeros caveat, mermaid FIPS 140-3 (140-2 legacy). deepseek's redirect *guess* (Red Hat 4.14) was wrong — orchestrator's deterministic curl proved it was the IEEE AMP URL. Verified clean: Kyverno graduated 2026-03-16, SPIFFE/Keylime/CoCo maturity, Vault PKCS#11 seal = Enterprise, OpenBao PKCS#11 supported. Re-verified T0/6527w/0-redirects. Build green PRIMARY 2171p. APPROVE.
