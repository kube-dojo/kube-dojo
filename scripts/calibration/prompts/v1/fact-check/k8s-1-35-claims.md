Verify these five claims about Kubernetes 1.35.

Output JSON exactly as:

```json
[
  {"claim_id": "C1", "verdict": "VERIFIED|FALSE|UNVERIFIABLE|NONEXISTENT", "rationale": "..."}
]
```

Do not guess. If you cannot find the claim in upstream docs, return
`UNVERIFIABLE`.

Claims:

- C1: PodSecurityPolicy is not available in Kubernetes 1.35.
- C2: `kubectl create secret generic` remains a supported way to create a
  Secret from literal values.
- C3: `ReadWriteOncePod` is a stable PersistentVolume access mode by the 1.35
  target.
- C4: Kubernetes 1.35 removed NetworkPolicy from the `networking.k8s.io` API.
- C5: In Kubernetes 1.35, `Deployment.spec.replicas` must be a quoted string.

