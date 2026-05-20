Given the failing pytest output and relevant manifest excerpt, identify the
root cause in one sentence and produce a minimal patch.

Failing test:

```text
E   AssertionError: namespace ResourceQuota requests.storage=300Gi is lower
E   than the PVC requests sum 320Gi, so the second PVC can remain Pending.
```

Relevant file excerpt from the Module 3.1 deployment fix path:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: llm-stack-quota
spec:
  hard:
    requests.cpu: "16"
    requests.memory: 96Gi
    requests.storage: 300Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: vllm-cache
spec:
  resources:
    requests:
      storage: 300Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qdrant-data
spec:
  resources:
    requests:
      storage: 20Gi
```

Return:

- root cause: one sentence
- patch: unified diff only for the minimal fix

