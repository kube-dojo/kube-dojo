# Review Audit: k8s/kca/module-1.1-advanced-kyverno-policies

**Path**: `src/content/docs/k8s/kca/module-1.1-advanced-kyverno-policies.md`
**First pass**: 2026-04-14T09:01:23Z
**Last pass**: 2026-04-14T09:01:23Z
**Total passes**: 1
**Current phase**: review
**Current reviewer**: -
**Current severity**: severe

---

## 2026-04-14T09:01:23Z — `WRITE`

**Writer**: gemini-3.1-pro-preview
**Mode**: rewrite
**Plan**: SEVERE REWRITE REQUIRED. Tier-1 integrity gate failed before structural review. Rewrite the module and resolve every integrity error.

Integrity errors:

- INVALID_YAML: line 344: expected '<document start>', but found '<scalar>'
  in "<unicode string>", line 5, column 1:
    "{{ contains(request.object.meta ... 
    ^
- INVALID_YAML: line 634: expected a single document in the stream
  in "<unicode string>", line 1, column 1:
    apiVersion: v1
    ^
but found another document
  in "<unicode st...
**Output**: 40234 chars
**Duration**: 5m 9s
## 2026-06-02T11:55:08Z — `REVIEW` — `APPROVE`
Tool-certs wave-2 KCA cross-family R1 (session 93). Reviewer: claude-opus-4.8. NEEDS_CHANGES 4.0 -> fixed via PR #1756. P1 lab JSON6902 add to nonexistent /metadata/labels parent -> materialize-map op; P1 external apiCall urlPath->service.url (in-cluster-API-only). P2 In/NotIn->AnyIn (deprecated v1.6), set-ops not glob, JMESPath all-containers. Ground-checked vs kyverno.io. Verifier T0/PASS bw5177.
