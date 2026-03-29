---
title: "Module 3.5: API Deprecations"
slug: k8s/ckad/part3-observability/module-3.5-api-deprecations
sidebar:
  order: 5
---
> **Complexity**: `[QUICK]` - Conceptual understanding with practical commands
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Understanding of Kubernetes API versioning

---

## Why This Module Matters

Kubernetes evolves rapidly. APIs that work today might be deprecated tomorrow and removed in future versions. Understanding API deprecations prevents broken manifests and failed deployments.

The CKAD exam tests:
- Awareness of deprecated APIs
- How to identify API versions for resources
- Updating manifests to use current APIs

> **The Road Construction Analogy**
>
> API deprecation is like road construction. First, signs warn you the road will close (deprecation). You have time to find alternate routes (new API version). Eventually, the old road closes completely (API removal). If you ignore the warnings, you're stuck when the road disappears.

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

### Quick Reference for Common Resources

| Resource | Current apiVersion |
|----------|-------------------|
| Pod | v1 |
| Service | v1 |
| ConfigMap | v1 |
| Secret | v1 |
| Deployment | apps/v1 |
| StatefulSet | apps/v1 |
| DaemonSet | apps/v1 |
| Job | batch/v1 |
| CronJob | batch/v1 |
| Ingress | networking.k8s.io/v1 |
| NetworkPolicy | networking.k8s.io/v1 |
| Role/RoleBinding | rbac.authorization.k8s.io/v1 |
| ClusterRole/ClusterRoleBinding | rbac.authorization.k8s.io/v1 |

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
| Using beta APIs in new manifests | Will break in future | Always use stable v1 |
| Copying old examples from internet | Deprecated APIs | Check version with `k explain` |
| Ignoring deprecation warnings | Manifests break after upgrade | Update immediately |
| Not knowing current versions | Time wasted in exam | Memorize common resources |

---

## Quiz

1. **How do you find the current API version for a resource?**
   <details>
   <summary>Answer</summary>
   `kubectl explain <resource>` or `kubectl api-resources | grep <resource>`
   </details>

2. **What's the current apiVersion for Ingress?**
   <details>
   <summary>Answer</summary>
   `networking.k8s.io/v1`
   </details>

3. **What's the current apiVersion for CronJob?**
   <details>
   <summary>Answer</summary>
   `batch/v1`
   </details>

4. **What happens when you use a removed API version?**
   <details>
   <summary>Answer</summary>
   The API server returns an error, and the resource cannot be created/updated.
   </details>

---

## Hands-On Exercise

**Task**: Practice finding and using correct API versions.

**Part 1: Discover API Versions**
```bash
# List all API resources
k api-resources | head -20

# Find specific resources
k api-resources | grep -i deployment
k api-resources | grep -i ingress
k api-resources | grep -i cronjob

# Use explain
k explain deployment
k explain ingress
k explain cronjob
```

**Part 2: Create Resources with Correct APIs**
```bash
# Create Deployment (apps/v1)
k create deploy api-test --image=nginx --dry-run=client -o yaml | head -10

# Generate CronJob (batch/v1)
k create cronjob api-cron --image=busybox --schedule="*/5 * * * *" -- echo hello --dry-run=client -o yaml | head -10
```

**Part 3: Verify Existing Resources**
```bash
# Check what version existing resources use
k get deployments -A -o jsonpath='{range .items[*]}{.apiVersion}{"\t"}{.metadata.name}{"\n"}{end}'
```

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
