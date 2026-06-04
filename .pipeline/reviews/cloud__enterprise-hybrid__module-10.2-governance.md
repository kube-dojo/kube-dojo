# Review Audit: cloud/enterprise-hybrid/module-10.2-governance

**Path**: `src/content/docs/cloud/enterprise-hybrid/module-10.2-governance.md`
**First pass**: 2026-04-14T10:31:12Z
**Last pass**: 2026-04-14T10:31:12Z
**Total passes**: 1
**Current phase**: review
**Current reviewer**: -
**Current severity**: severe

---

## 2026-04-14T10:31:12Z — `WRITE`

**Writer**: gemini-3.1-pro-preview
**Mode**: rewrite
**Plan**: SEVERE REWRITE REQUIRED. Tier-1 integrity gate failed before structural review. Rewrite the module and resolve every integrity error.

Integrity errors:

- INVALID_YAML: line 231: expected a single document in the stream
  in "<unicode string>", line 2, column 1:
    constraint: constraints/containe ... 
    ^
but found another document
  in "<unicode string>", line 6, column 1:
    ---
    ^
- INVALID_YAML: line 309: expected a single document in the stream
  in "<unicode string>", line 2, colu...
**Output**: 49471 chars
**Duration**: 1m 55s
## 2026-06-04T14:57:35Z — `REVIEW` — `APPROVE`
Cloud / Enterprise & Hybrid expand-to-floor wave (session 103). Reviewer: claude-opus-4.8 (cross-family). P1 fabricated constraints/container.restrictPublicCluster x3 -> custom constraint; P2 ECR lifecycle-policy mislabeled as signing, Azure Policy ADD-ON vs Arc EXTENSION, SCP ForAllValues:StringNotLike footgun -> ArnNotLike, GCP CustomConstraint methodTypes, Kyverno validationFailureAction deprecation. PRESERVED (web-verified): Kyverno CNCF Graduated 2026-03, eks:endpointPublicAccess SCP key (AWS Apr-2026). Verifier T0/PASS; orchestrator web-verified key facts + ground-checked all fixes; PR #1788.
