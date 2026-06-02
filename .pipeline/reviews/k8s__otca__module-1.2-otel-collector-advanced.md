# Review Audit: k8s/otca/module-1.2-otel-collector-advanced

**Path**: `src/content/docs/k8s/otca/module-1.2-otel-collector-advanced.md`
**First pass**: 2026-04-14T13:37:22Z
**Last pass**: 2026-04-14T13:37:22Z
**Total passes**: 1
**Current phase**: write
**Current reviewer**: gemini
**Current severity**: clean

---

## 2026-04-14T13:37:22Z — `RESET`

**New phase**: write
**Cleared errors**:
- Deterministic checks failed after review
## 2026-06-02T11:38:43Z — `REVIEW` — `APPROVE`
Tool-certs wave-2 OTCA cross-family R1 (session 93). Reviewer: claude-opus-4.8. NEEDS_CHANGES 4.0 -> fixed via PR #1755. P1 connector/count schema-invalid (traces: wrapper + name: list) -> map keyed by metric name (web-verified vs countconnector README). P2 Instrumentation CRD served v1alpha1 not v1alpha2 (OpenTelemetryCollector has v1beta1); broken Next-Module link fixed; otlp/loki->otlphttp (Loki HTTP-only). Verifier T0/PASS bw5177.
