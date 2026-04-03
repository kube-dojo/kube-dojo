---
title: "Module 3.5: API Deprecations"
slug: k8s/ckad/part3-observability/module-3.5-api-deprecations
sidebar:
  order: 5
lab:
  id: ckad-3.5-api-deprecations
  url: https://killercoda.com/kubedojo/scenario/ckad-3.5-api-deprecations
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[QUICK]` - Conceptual understanding with practical commands
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Understanding of Kubernetes API versioning

---

## Learning Outcomes

After completing this module, you will be able to:
- **Diagnose** a failed `kubectl apply` caused by a removed API and fix it in under 2 minutes
- **Find** the correct API version for any resource using `kubectl explain` and `kubectl api-resources`
- **Update** a deprecated manifest to the current API version, including structural changes
- **Explain** the Kubernetes deprecation policy and what guarantees it provides

---

## Why This Module Matters

It was 2 AM on a Tuesday when the on-call engineer at a fintech startup ran `kubectl apply -f deploy/` after upgrading their cluster from 1.21 to 1.22. Every single Ingress resource failed. The CI/CD pipeline that had been deploying fine for two years was suddenly broken — 14 microservices went down because every manifest still used `networking.k8s.io/v1beta1`. The team had ignored deprecation warnings in their server logs for three releases. Total downtime: 3 hours. Revenue lost: $180K.

This wasn't a bug. It was entirely preventable. The API server had been printing warnings for over a year.

> **The Road Construction Analogy**
>
> API deprecation is like road construction. First, signs warn you the road will close (deprecation). You have time to find alternate routes (new API version). Eventually, the old road closes completely (API removal). If you ignore the warnings, you're stuck when the road disappears.

**The key skill isn't memorizing API versions** — it's knowing how to look them up instantly with `kubectl explain`. The exam cluster might be a different version than what you practiced on. The commands always work.

---

## API Versioning Basics

### Version Stages

| Stage | Meaning | Stability |
|-------|---------|-----------|
| `alpha` (v1alpha1) | Experimental, may change or disappear | Unstable |
| `beta` (v1beta1) | Feature complete, may change | Mostly stable |
| `stable` (v1, v2) | Production ready, backward compatible | Stable |

### Version Progression

```
v1alpha1 → v1alpha2 → v1beta1 → v1beta2 → v1
```

### API Groups

```yaml
# Core group (no prefix)
apiVersion: v1
kind: Pod

# Named groups
apiVersion: apps/v1
kind: Deployment

apiVersion: networking.k8s.io/v1
kind: Ingress

apiVersion: batch/v1
kind: Job
```

---

## Common Deprecations

### Historical Examples

| Old API | Current API | Removed In |
|---------|-------------|------------|
| `extensions/v1beta1 Ingress` | `networking.k8s.io/v1` | 1.22 |
| `apps/v1beta1 Deployment` | `apps/v1` | 1.16 |
| `rbac.authorization.k8s.io/v1beta1` | `rbac.authorization.k8s.io/v1` | 1.22 |
| `networking.k8s.io/v1beta1 IngressClass` | `networking.k8s.io/v1` | 1.22 |
| `batch/v1beta1 CronJob` | `batch/v1` | 1.25 |
| `policy/v1beta1 PodSecurityPolicy` | Removed (use Pod Security Admission) | 1.25 |

### Current Exam Environment

The CKAD exam uses recent Kubernetes versions. Most beta APIs have been removed. Always use stable (`v1`) versions.

---

## Finding Correct API Versions

### List API Resources

```bash
# All resources with API versions
k api-resources

# Specific resource
k api-resources | grep -i deployment
# Output: deployments   deploy   apps/v1   true   Deployment

# With short names
k api-resources --sort-by=name
```

### Explain Command

```bash
# Get API version for a resource
k explain deployment
# Output shows: VERSION: apps/v1

k explain ingress
# Output shows: VERSION: networking.k8s.io/v1

k explain cronjob
# Output shows: VERSION: batch/v1
```

### Get Current Objects

```bash
# See what version existing objects use
k get deployment nginx -o yaml | head -5
# apiVersion: apps/v1
# kind: Deployment
```

---

## Checking for Deprecated APIs

### kubectl Convert (if available)

```bash
# Convert old manifest to new API
kubectl convert -f old-deployment.yaml --output-version apps/v1
```

Note: `kubectl convert` may not be available in all environments.

> **Stop and think**: You find a working Kubernetes manifest in your company's git repo that was last modified in 2020. Would you trust its `apiVersion` field on a 2026 cluster? What's the fastest way to verify it?

### Manual Check

```bash
# Check what the manifest uses
head -5 my-manifest.yaml

# Compare with current API
k api-resources | grep -i <resource-type>
```

### API Server Warnings

When you apply a deprecated API, the server warns you:

```bash
$ k apply -f old-ingress.yaml
Warning: networking.k8s.io/v1beta1 Ingress is deprecated in v1.19+,
unavailable in v1.22+; use networking.k8s.io/v1 Ingress
```

---

## Updating Manifests

### Example: Ingress Update

**Old (deprecated):**
```yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: my-ingress
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        backend:
          serviceName: my-service
          servicePort: 80
```

**New (current):**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

> **Pause and predict**: Looking at the old and new Ingress specs above, can you spot all three structural changes? Try listing them before reading the summary below.

### Key Changes Often Required

1. **apiVersion** - Update to stable version
2. **spec structure** - May change between versions
3. **New required fields** - Like `pathType` for Ingress

---

## Exam Strategy

### Before Writing YAML

```bash
# Always check current API version first
k explain <resource>

# Example
k explain ingress
k explain cronjob
k explain networkpolicy
```

### Don't Memorize — Look It Up

You might be tempted to memorize API versions for every resource. Don't. The exam environment might use a different Kubernetes version than what you studied. Instead, build muscle memory for the lookup:

```bash
# This is the ONLY command you need to remember
k explain <resource> | head -5

# Practice: what happens if you guess wrong?
# Try applying a manifest with the wrong version and read the error.
```

> **Pause and predict**: If you applied a Deployment with `apiVersion: extensions/v1beta1` on a 1.35 cluster, what would happen? Would it warn you, error out, or silently succeed? Think about it before reading on.

The answer: it would error out immediately. `extensions/v1beta1` Deployments were removed in 1.16 — that's almost 20 versions ago. The error message would say `no matches for kind "Deployment" in version "extensions/v1beta1"`. This is different from a deprecation warning, which only appears for APIs that still work but are scheduled for removal.

---

## Deprecation Policy

### Kubernetes Guarantees

1. **Beta APIs deprecated at least 3 releases** before removal
2. **Stable APIs almost never removed** (only in major version changes)
3. **Deprecation warnings** shown in API server responses

### Timeline Example

```
1.19: v1beta1 deprecated (warning)
1.20: v1beta1 still works (warning continues)
1.21: v1beta1 still works (warning continues)
1.22: v1beta1 REMOVED (error if used)
```

---

## Did You Know?

- **PodSecurityPolicy was completely removed** in Kubernetes 1.25. It was replaced by Pod Security Admission, which works differently.

- **The `kubectl convert` plugin** can convert between API versions, but it's not installed by default and may not be on the exam.

- **CRDs can have their own deprecation** schedule set by the operator/vendor who created them.

- **Running `kubectl apply` with deprecated APIs** still works until removal, but you'll get warnings every time.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Copying YAML from old blog posts or Stack Overflow | Examples from 2019 use removed APIs (`extensions/v1beta1`) | Always verify with `k explain` on YOUR cluster |
| Ignoring deprecation warnings in CI/CD logs | Warnings become errors after 3 releases — but the upgrade happens silently | Treat deprecation warnings as bugs; fix in the next sprint |
| Memorizing API versions instead of learning the lookup | Exam cluster version may differ from what you studied | Build muscle memory for `k explain <resource>` — takes 3 seconds |
| Only updating `apiVersion` without checking spec changes | Ingress, CronJob, and others changed their spec structure between versions | Always run `k explain <resource>.spec` after changing apiVersion |
| Not testing manifests after a cluster upgrade | Old manifests silently become time bombs | Add `kubectl apply --dry-run=server` to your CI pipeline |
| Using `kubectl convert` without understanding the changes | `convert` handles apiVersion but may miss structural changes | Use `convert` as a starting point, then verify with `explain` |

---

## Quiz

1. **Your team just upgraded a cluster from 1.24 to 1.25. Deployments work fine but all CronJobs fail to apply. What's likely wrong and how would you fix it?**
   <details>
   <summary>Answer</summary>
   CronJob moved from `batch/v1beta1` to `batch/v1` and `v1beta1` was removed in 1.25. The manifests still reference the old API version. Fix: run `k explain cronjob | head -5` to confirm the current version, then update every CronJob manifest's `apiVersion` to `batch/v1`. Also check if the CronJob spec structure changed between versions — in this case, it didn't significantly, but always verify with `k explain cronjob.spec`.
   </details>

2. **You run `kubectl apply -f ingress.yaml` and get: `no matches for kind "Ingress" in version "extensions/v1beta1"`. But your colleague says "it worked last week." What happened?**
   <details>
   <summary>Answer</summary>
   The cluster was upgraded between last week and now. `extensions/v1beta1` Ingresses were removed in Kubernetes 1.22. Before that version, the API still worked but printed deprecation warnings. After the upgrade crossed that boundary, the API was completely removed. The fix isn't just changing the apiVersion to `networking.k8s.io/v1` — you also need to update the spec structure: `backend.serviceName` becomes `backend.service.name`, `backend.servicePort` becomes `backend.service.port.number`, and you must add `pathType: Prefix` (or `Exact`).
   </details>

3. **You're writing a manifest during the CKAD exam and you're not sure if NetworkPolicy uses `v1` or `v1beta1`. What's the fastest way to find out, and why shouldn't you guess?**
   <details>
   <summary>Answer</summary>
   Run `k explain networkpolicy | head -5` — this shows the current VERSION on the exam cluster, which may differ from what you studied. Guessing is risky because the exam uses a specific Kubernetes version that you won't know in advance. Even if you memorized versions for 1.35, the exam might use 1.34 or 1.36. The `explain` command always gives you the truth for the cluster you're on. It takes 3 seconds and eliminates a category of errors entirely.
   </details>

4. **Your CI pipeline applies manifests with `kubectl apply --server-side`. The server returns `Warning: batch/v1beta1 CronJob is deprecated`. The manifests still apply successfully. Should you fix this now or later?**
   <details>
   <summary>Answer</summary>
   Fix it now. A deprecation warning means the API still works in the current version but has a removal date. Kubernetes guarantees at least 3 releases between deprecation and removal, so you have time — but ignoring it means your manifests will break silently during a future upgrade. The safest approach: update the apiVersion immediately, verify the spec structure hasn't changed, test in staging, and update all copies of the manifest (Helm charts, Kustomize bases, GitOps repos). The cost of fixing now is 5 minutes; the cost of fixing during a 2 AM outage after an upgrade is hours.
   </details>

5. **You find a Stack Overflow answer from 2019 that shows how to create a Deployment using `apiVersion: extensions/v1beta1`. Can you trust it? How would you adapt it?**
   <details>
   <summary>Answer</summary>
   You cannot trust the apiVersion from any online example — only `kubectl explain` on your actual cluster tells you the truth. `extensions/v1beta1` Deployments were removed in Kubernetes 1.16 (released 2019). To adapt: change `apiVersion` to `apps/v1`, then verify the spec structure with `k explain deployment.spec`. For Deployments, the v1 spec is essentially the same as v1beta1, so the rest of the manifest likely works. For other resources like Ingress, the spec changed significantly between versions. Always validate with `--dry-run=client -o yaml` before applying.
   </details>

6. **What's the difference between a "deprecated" API and a "removed" API? Why does this distinction matter for your workflow?**
   <details>
   <summary>Answer</summary>
   A deprecated API still works — the server accepts it and processes it, but prints a warning in the response. A removed API is gone — the server returns an error and refuses the request. This distinction matters because deprecated APIs give you a grace period (minimum 3 releases) to update. During this window, everything works but you're on borrowed time. Removed APIs cause immediate failures. The practical implication: if you see deprecation warnings in your CI/CD logs, treat them as non-critical bugs to fix in the next sprint. If you see removal errors, it's a production incident.
   </details>

---

## Hands-On Exercise: Fix the Broken Manifests

**Scenario**: You've inherited a repository of Kubernetes manifests from a team that left the company. The manifests were last updated for Kubernetes 1.21. Your cluster runs 1.35. Some manifests will fail to apply. Your job: find what's broken, fix it, and verify it works.

**Part 1: Diagnose the Problem**

Save this broken manifest as `broken-ingress.yaml`:
```yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: legacy-app
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        backend:
          serviceName: api-service
          servicePort: 8080
      - path: /
        backend:
          serviceName: frontend
          servicePort: 80
```

Try to apply it: `k apply -f broken-ingress.yaml --dry-run=server`

What error do you get? Read it carefully — it tells you exactly what's wrong.

<details>
<summary>Expected error</summary>

```
error: resource mapping not found for name: "legacy-app" namespace: "" from "broken-ingress.yaml":
no matches for kind "Ingress" in version "networking.k8s.io/v1beta1"
```

This means `v1beta1` has been completely removed. You need `networking.k8s.io/v1`.
</details>

**Part 2: Fix the Manifest**

Update `broken-ingress.yaml` to use the correct API version. Hint: the spec structure ALSO changed — use `k explain ingress.spec.rules.http.paths` to see the current structure.

<details>
<summary>Fixed manifest</summary>

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: legacy-app
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

Key changes: `apiVersion` updated, `pathType: Prefix` added (now required), `backend` structure completely changed from flat to nested (`service.name` and `service.port.number`).
</details>

**Part 3: Audit All Resources**

Run this to check all API versions available on your cluster:
```bash
# Find the current version for every resource you commonly use
for res in pod service deployment statefulset daemonset job cronjob ingress networkpolicy; do
  version=$(k explain $res 2>/dev/null | grep "VERSION:" | awk '{print $2}')
  echo "$res: $version"
done
```

**Part 4: Generate Correct YAML from Scratch**

Without looking at any reference, generate correct manifests using imperative commands:
```bash
k create deploy audit-app --image=nginx --dry-run=client -o yaml > deployment.yaml
k create job audit-job --image=busybox -- echo done --dry-run=client -o yaml > job.yaml
k create cronjob audit-cron --image=busybox --schedule="0 * * * *" -- echo check --dry-run=client -o yaml > cronjob.yaml
```

Verify each one: `grep apiVersion *.yaml`

**Success Criteria**:
- [ ] Broken ingress manifest diagnosed and fixed
- [ ] Fixed manifest applies successfully with `--dry-run=server`
- [ ] You can explain the 3 structural changes between v1beta1 and v1 Ingress
- [ ] You can look up any resource's API version in under 10 seconds

---

## Practice Drills

### Drill 1: API Resources (Target: 2 minutes)

```bash
# Find API version for various resources
k explain pod | head -5
k explain service | head -5
k explain deployment | head -5
k explain ingress | head -5
k explain networkpolicy | head -5
```

### Drill 2: API Resource List (Target: 2 minutes)

```bash
# List resources and their groups
k api-resources --sort-by=name | grep -E "^NAME|deployment|ingress|job|cronjob"
```

### Drill 3: Generate Correct YAML (Target: 3 minutes)

```bash
# Generate manifests and verify API versions

# Deployment
k create deploy drill3-deploy --image=nginx --dry-run=client -o yaml | grep apiVersion

# Job
k create job drill3-job --image=busybox -- echo done --dry-run=client -o yaml | grep apiVersion

# CronJob
k create cronjob drill3-cron --image=busybox --schedule="* * * * *" -- echo hi --dry-run=client -o yaml | grep apiVersion
```

### Drill 4: Identify Resource Groups (Target: 2 minutes)

```bash
# Which group does each belong to?
k api-resources | grep -E "^NAME|^deployments|^services|^ingresses|^networkpolicies"

# Expected:
# deployments - apps
# services - core (no group)
# ingresses - networking.k8s.io
# networkpolicies - networking.k8s.io
```

### Drill 5: Full Version Lookup (Target: 3 minutes)

**Scenario**: You need to write YAML for multiple resources. Find the correct API versions.

```bash
# Resources needed: Deployment, Service, Ingress, ConfigMap, Secret, NetworkPolicy

# Quick lookup
for res in deployment service ingress configmap secret networkpolicy; do
  echo -n "$res: "
  k explain $res 2>/dev/null | grep "VERSION:" | awk '{print $2}'
done
```

---

## Part 3 Summary

You've completed the Application Observability and Maintenance section:

- **Module 3.1**: Probes - Health checking with liveness, readiness, startup
- **Module 3.2**: Logging - Accessing container logs
- **Module 3.3**: Debugging - Systematic troubleshooting workflow
- **Module 3.4**: Monitoring - Resource usage with kubectl top
- **Module 3.5**: API Deprecations - Using current API versions

---

## Next Steps

Take the [Part 3 Cumulative Quiz](../part3-cumulative-quiz/) to test your understanding, then proceed to [Part 4: Application Environment, Configuration and Security](../part4-environment/module-4.1-configmaps/).
