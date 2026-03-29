---
title: "Module 0.4: kubernetes.io Navigation"
slug: k8s/cka/part0-environment/module-0.4-k8s-docs
sidebar:
  order: 4
---
> **Complexity**: `[QUICK]` - Know where things are, find them fast
>
> **Time to Complete**: 20-30 minutes
>
> **Prerequisites**: None

---

## Why This Module Matters

During the CKA exam, you have access to:
- **kubernetes.io/docs**
- **kubernetes.io/blog**
- **helm.sh/docs** (for Helm)
- **github.com/kubernetes** (for reference)

This is open-book. You don't need to memorize YAML schemas. But if you spend 3 minutes searching for a NetworkPolicy example, you've wasted half your question time.

This module teaches you where everything is—so you can find it in seconds.

> **The Library Analogy**
>
> Imagine you need a specific recipe from a library. You could wander the aisles hoping to stumble upon it. Or you could know that cookbooks are in section 641.5, third shelf from the top. The kubernetes.io docs are your library. Wandering wastes time. Knowing the sections—Tasks for how-to, Reference for specs, Concepts for theory—is your Dewey Decimal System. This module gives you the map.

> **War Story: The Search That Cost 8 Points**
>
> A candidate needed a NetworkPolicy example during their CKA. They typed "network policy" in the search bar and got dozens of results. They clicked through Concepts first (wrong—theory, no examples), then a blog post (interesting but not what they needed), then finally found the Tasks page. Total time: 4 minutes. They ran out of time on the last question. Later they learned: Tasks → Administer Cluster → Declare Network Policy. That's a 15-second lookup if you know the path.

---

## Part 1: Documentation Structure

The Kubernetes documentation has a predictable structure:

```
kubernetes.io/docs/
├── concepts/           ← Theory, how things work
├── tasks/              ← Step-by-step HOW-TO guides
├── reference/          ← API specs, kubectl, glossary
└── tutorials/          ← End-to-end walkthroughs
```

### What You'll Use in the Exam

| Section | Use For | Example |
|---------|---------|---------|
| **Tasks** | How to DO something | "Configure a Pod to Use a ConfigMap" |
| **Reference** | YAML fields, kubectl flags | "kubectl Cheat Sheet" |
| **Concepts** | Understanding (rarely during exam) | "What is a Service?" |

**Tasks** is your primary destination during the exam.

---

## Part 2: Bookmark These URLs

These are the pages you'll visit most. Bookmark them now.

### Must-Have Bookmarks

| Topic | URL |
|-------|-----|
| **kubectl Cheat Sheet** | https://kubernetes.io/docs/reference/kubectl/cheatsheet/ |
| **Tasks (main page)** | https://kubernetes.io/docs/tasks/ |
| **Workloads** | https://kubernetes.io/docs/concepts/workloads/ |
| **Networking** | https://kubernetes.io/docs/concepts/services-networking/ |
| **Storage** | https://kubernetes.io/docs/concepts/storage/ |
| **Configuration** | https://kubernetes.io/docs/concepts/configuration/ |

### High-Value Task Pages

| Need | Go To |
|------|-------|
| Create ConfigMap | Tasks → Configure Pods → Configure ConfigMaps |
| Create Secret | Tasks → Configure Pods → Secrets |
| Create PVC | Tasks → Configure Pods → Configure PersistentVolumeClaim |
| NetworkPolicy | Tasks → Administer Cluster → Network Policies |
| RBAC | Tasks → Administer Cluster → Using RBAC Authorization |
| Ingress | Tasks → Access Applications → Set Up Ingress |
| HPA | Tasks → Run Applications → Horizontal Pod Autoscale |

### New in 2025 - Know These

| Topic | URL |
|-------|-----|
| **Gateway API** | https://kubernetes.io/docs/concepts/services-networking/gateway/ |
| **Helm** | https://helm.sh/docs/ |
| **Kustomize** | https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/ |

---

## Part 3: Search Strategy

The built-in search works, but it's often faster to know where things are.

### Strategy 1: Use the Search Bar

1. Press `/` or click the search icon
2. Type keywords: "networkpolicy example"
3. Look for **Tasks** results first

### Strategy 2: Go Directly to Tasks

Most exam answers are in Tasks:

```
kubernetes.io/docs/tasks/
├── Administer a Cluster/
│   ├── Network Policies
│   ├── Using RBAC Authorization
│   └── Manage Resources
├── Configure Pods and Containers/
│   ├── Configure a Pod to Use a ConfigMap
│   ├── Configure a Pod to Use a Secret
│   └── Configure a Pod to Use a PersistentVolume
├── Access Applications in a Cluster/
│   └── Set up Ingress on Minikube with NGINX
└── Run Applications/
    └── Horizontal Pod Autoscaling
```

### Strategy 3: kubectl explain

Faster than any website:

```bash
# See available fields for a resource
k explain pod.spec.containers

# Go deeper
k explain pod.spec.containers.resources
k explain pod.spec.containers.volumeMounts

# See all fields at once
k explain pod --recursive | grep -A5 "containers"
```

This works offline and shows exactly what fields are available.

---

## Part 4: Finding YAML Examples

### Pattern: Every Task Has Examples

When you find a task page, scroll down. There's almost always a copyable YAML example.

Example: "Configure a Pod to Use a ConfigMap"
- Scroll to "Define container environment variables using ConfigMap data"
- Copy the YAML
- Modify for your needs

### Pattern: Look for "What's next" Section

At the bottom of pages, "What's next" links to related tasks. If you're close but not quite right, check these links.

### Pattern: API Reference for Field Details

Need to know all PVC accessModes?

```
kubernetes.io/docs/reference/kubernetes-api/
├── Workload Resources/
├── Service Resources/
├── Config and Storage Resources/
│   └── PersistentVolumeClaim
└── ...
```

Or faster:
```bash
k explain pvc.spec.accessModes
```

---

## Part 5: Quick Reference Locations

### NetworkPolicy

**Location**: Tasks → Administer a Cluster → Declare Network Policy

**Direct URL**: https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/

**Key Example**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-network-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 6379
```

### PersistentVolumeClaim

**Location**: Tasks → Configure Pods → Configure a Pod to Use a PersistentVolumeClaim

**Key Example**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### RBAC (Role + RoleBinding)

**Location**: Tasks → Administer a Cluster → Using RBAC Authorization

**Key Example**:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### Ingress

**Location**: Concepts → Services, Load Balancing → Ingress

**Key Example**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: minimal-ingress
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

### Gateway API (New in 2025)

**Location**: Concepts → Services, Load Balancing → Gateway API

**Key Example**:
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: http-route
spec:
  parentRefs:
  - name: my-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /app
    backendRefs:
    - name: my-service
      port: 80
```

---

## Part 6: Speed Drills

Practice finding these as fast as possible:

### Drill 1: Find NetworkPolicy Example (Target: <30 seconds)
1. Go to kubernetes.io
2. Search "network policy"
3. Click first Tasks result
4. Scroll to YAML example

### Drill 2: Find PVC Access Modes (Target: <20 seconds)
```bash
k explain pvc.spec.accessModes
```
Or search "PVC accessModes"

### Drill 3: Find RBAC Role Example (Target: <30 seconds)
1. Search "RBAC"
2. Click "Using RBAC Authorization"
3. Find "Role example"

### Drill 4: Find Helm Install Syntax (Target: <30 seconds)
1. Go to helm.sh/docs
2. Search "install"
3. Find `helm install` command reference

---

## Did You Know?

- **The exam browser has limited tabs**. You can't open 20 tabs like normal browsing. Learn to navigate efficiently with fewer tabs.

- **kubernetes.io search is decent but not great**. Sometimes Google would be better, but you can't use it in the exam. Practice using the native search.

- **`kubectl explain` doesn't need internet**. It reads from your cluster's API server. This is often faster than searching documentation.

- **Blog posts are allowed** (kubernetes.io/blog). Some complex topics have excellent blog explanations. But Tasks is usually faster for "how do I do X."

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Searching too broadly | Too many results | Use specific terms: "networkpolicy ingress example" |
| Reading concepts during exam | Wastes time | Go straight to Tasks |
| Memorizing YAML | Unnecessary | Know WHERE to find examples |
| Not using kubectl explain | Slow | `k explain` is instant |
| Opening too many tabs | Browser slows down | Close tabs you're done with |

---

## Quiz

1. **Where do you find step-by-step guides for specific tasks?**
   <details>
   <summary>Answer</summary>
   kubernetes.io/docs/tasks/ — The Tasks section contains how-to guides with examples.
   </details>

2. **What's the fastest way to see available fields for a PVC spec?**
   <details>
   <summary>Answer</summary>
   `kubectl explain pvc.spec` — Works offline, shows all fields with descriptions.
   </details>

3. **You need a Gateway API HTTPRoute example. Where do you look?**
   <details>
   <summary>Answer</summary>
   kubernetes.io/docs/concepts/services-networking/gateway/ — Gateway API docs with examples.
   </details>

4. **The search returns too many results for "network policy." How do you narrow it down?**
   <details>
   <summary>Answer</summary>
   Add specifics: "network policy ingress example" or go directly to Tasks → Administer Cluster → Network Policies.
   </details>

---

## Hands-On Exercise

**Task**: Practice finding documentation quickly.

**Timed Challenges** (use a stopwatch):

1. **Find ConfigMap example** (Target: <30 sec)
   - Find a complete ConfigMap YAML in the docs

2. **Find Secret from file example** (Target: <45 sec)
   - Find how to create a Secret from a file

3. **Find all PVC accessModes** (Target: <15 sec)
   - Use `kubectl explain`

4. **Find HPA example** (Target: <45 sec)
   - Find a complete HorizontalPodAutoscaler YAML

5. **Find Helm upgrade command** (Target: <30 sec)
   - Find the `helm upgrade` documentation

**Success Criteria**:
- [ ] Can find ConfigMap task page in <30 seconds
- [ ] Can find any YAML example in <1 minute
- [ ] Know how to use kubectl explain
- [ ] Know the difference between Tasks and Concepts

---

## Practice Drills

### Drill 1: Documentation Race (Target times provided)

Open kubernetes.io and race to find these. Use a stopwatch.

| Task | Target Time |
|------|-------------|
| Find NetworkPolicy YAML example | < 30 sec |
| Find PVC with ReadWriteMany example | < 45 sec |
| Find RBAC RoleBinding example | < 30 sec |
| Find Ingress with TLS example | < 45 sec |
| Find HorizontalPodAutoscaler example | < 45 sec |
| Find Job with backoffLimit example | < 30 sec |

Record your times. Repeat until you beat all targets.

### Drill 2: kubectl explain Mastery (Target: 2 minutes total)

Without using the web, find these using only `kubectl explain`:

```bash
# 1. What fields does a Pod spec have?
kubectl explain pod.spec | head -30

# 2. What are valid values for PVC accessModes?
kubectl explain pvc.spec.accessModes

# 3. What fields does a container have for health checks?
kubectl explain pod.spec.containers.livenessProbe

# 4. What's the structure of a NetworkPolicy spec?
kubectl explain networkpolicy.spec

# 5. How do you specify resource limits?
kubectl explain pod.spec.containers.resources
```

### Drill 3: Find and Apply (Target: 5 minutes)

Using ONLY kubernetes.io docs, find examples and create:

```bash
# 1. Find a ConfigMap example and create one
# kubernetes.io → Tasks → Configure Pods → ConfigMaps

# 2. Find a Secret example and create one
# kubernetes.io → Tasks → Configure Pods → Secrets

# 3. Find a NetworkPolicy example and create one
# kubernetes.io → Tasks → Administer Cluster → Network Policies

# Verify all three exist
kubectl get cm,secret,netpol

# Cleanup
kubectl delete cm --all
kubectl delete secret --all  # careful: leaves default secrets
kubectl delete netpol --all
```

### Drill 4: Helm Documentation Hunt (Target: 3 minutes)

Find these on helm.sh/docs:

```bash
# 1. How do you install a chart from a repo?
# Answer: helm install [RELEASE] [CHART]

# 2. How do you see values available for a chart?
# Answer: helm show values [CHART]

# 3. How do you rollback to a previous release?
# Answer: helm rollback [RELEASE] [REVISION]

# 4. How do you list all releases?
# Answer: helm list

# 5. How do you upgrade with new values?
# Answer: helm upgrade [RELEASE] [CHART] -f values.yaml
```

### Drill 5: Gateway API Deep Dive (Target: 5 minutes)

Gateway API is new to CKA 2025. Find these in the docs:

```bash
# 1. Find the HTTPRoute example
# kubernetes.io → Concepts → Services → Gateway API

# 2. Find what parentRefs means in HTTPRoute
kubectl explain httproute.spec.parentRefs  # If Gateway API CRDs installed

# 3. Find the difference between Gateway and HTTPRoute
# Gateway = infrastructure (like LoadBalancer)
# HTTPRoute = routing rules (like Ingress rules)
```

### Drill 6: Troubleshooting - Wrong Documentation

**Scenario**: You found what looks like the right YAML but it doesn't work.

```bash
# You found this "Ingress" example but it fails
cat << 'EOF' > wrong-ingress.yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: test-ingress
spec:
  backend:
    serviceName: testsvc
    servicePort: 80
EOF

kubectl apply -f wrong-ingress.yaml
# ERROR: no matches for kind "Ingress" in version "extensions/v1beta1"

# YOUR TASK: Find the CORRECT API version in current docs
# Hint: The docs example is outdated. Find current version.
```

<details>
<summary>Solution</summary>

The old `extensions/v1beta1` API was deprecated. Current version:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ingress
spec:
  defaultBackend:
    service:
      name: testsvc
      port:
        number: 80
```

**Lesson**: Always check the apiVersion in docs matches your cluster version. Use `kubectl api-resources | grep ingress` to see available versions.

</details>

### Drill 7: Speed Documentation Challenge

Set a 10-minute timer. Complete as many as possible:

1. [ ] Create a Pod with resource limits (find in docs)
2. [ ] Create a Deployment with 3 replicas (find in docs)
3. [ ] Create a Service type LoadBalancer (find in docs)
4. [ ] Create a ConfigMap from a file (find in docs)
5. [ ] Create a PVC with 1Gi storage (find in docs)
6. [ ] Create a Job that runs once (find in docs)
7. [ ] Create a CronJob running every minute (find in docs)
8. [ ] Create a NetworkPolicy allowing only port 80 (find in docs)

```bash
# Validate each one works
kubectl apply -f <file> --dry-run=client
```

Score: How many did you complete in 10 minutes?
- 8: Excellent - exam ready
- 6-7: Good - keep practicing
- 4-5: Needs work - repeat drill daily
- <4: Review documentation structure again

---

## Next Module

[Module 0.5: Exam Strategy - Three-Pass Method](../module-0.5-exam-strategy/) - The strategy that maximizes your score.
