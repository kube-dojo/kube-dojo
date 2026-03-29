---
title: "Module 0.1: CKAD Overview & Strategy"
slug: k8s/ckad/part0-environment/module-0.1-ckad-overview
sidebar:
  order: 1
---
> **Complexity**: `[QUICK]` - Orientation and strategy
>
> **Time to Complete**: 20-30 minutes
>
> **Prerequisites**: CKA curriculum completed (recommended) or Kubernetes fundamentals

---

## Why This Module Matters

The CKAD (Certified Kubernetes Application Developer) certification proves you can design, build, configure, and expose cloud-native applications for Kubernetes. Unlike the CKA which focuses on cluster administration, the CKAD is all about **the developer experience**—how to package, deploy, debug, and run applications.

If you've completed the CKA curriculum, you already know about 60% of what's on the CKAD. This certification takes that foundation and zooms in on the developer-facing aspects: multi-container pod patterns, probes, Jobs, debugging, and API deprecation awareness.

> **The Chef vs Restaurant Manager Analogy**
>
> CKA is like being a restaurant manager—you ensure the kitchen works (cluster), the staff is scheduled (nodes), supplies are stocked (storage), and customers can reach you (networking). CKAD is like being the chef—you focus on creating the dishes (applications), getting ingredients (configuration), timing everything perfectly (probes), and handling special orders (Jobs). Both need to understand the kitchen, but from different perspectives.

---

## CKAD vs CKA: Key Differences

| Aspect | CKA | CKAD |
|--------|-----|------|
| **Focus** | Cluster administration | Application development |
| **Perspective** | Ops/Platform team | Dev/Application team |
| **Exam Duration** | 2 hours | 2 hours |
| **Passing Score** | 66% | 66% |
| **Questions** | ~15-20 tasks | ~15-20 tasks |
| **Clusters** | Multiple contexts | Multiple contexts |

### What's Shared (~60%)

If you did the CKA, you can breeze through:
- Pods, Deployments, ReplicaSets
- Services (ClusterIP, NodePort, LoadBalancer)
- ConfigMaps and Secrets
- PersistentVolumes and PersistentVolumeClaims
- Basic Networking and NetworkPolicies
- Helm and Kustomize basics
- RBAC fundamentals

### What's New/Emphasized in CKAD

The CKAD puts extra weight on developer-specific topics:

| Topic | CKA Coverage | CKAD Coverage |
|-------|-------------|---------------|
| **Multi-container pods** | Mentioned | Deep focus |
| **Init containers** | Mentioned | Essential skill |
| **Probes** (liveness/readiness/startup) | Basic | Detailed |
| **Jobs & CronJobs** | Covered | Developer focus |
| **Container image building** | Not covered | Important |
| **API deprecations** | Not covered | Exam topic |
| **Debugging applications** | From admin view | From dev view |
| **Deployment strategies** | Rolling updates | Blue/green, canary |

---

## CKAD Exam Domains (2025)

The exam is divided into five weighted domains:

```
┌──────────────────────────────────────────────────────────────────┐
│                    CKAD Exam Breakdown                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Application Environment, Configuration & Security   25%  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────┐ ┌───────────────────────────┐   │
│  │ Application Design & Build │ │ Application Deployment    │   │
│  │            20%             │ │           20%             │   │
│  └────────────────────────────┘ └───────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────┐ ┌───────────────────────────┐   │
│  │ Services & Networking      │ │ Observability/Maintenance │   │
│  │            20%             │ │           15%             │   │
│  └────────────────────────────┘ └───────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Domain 1: Application Design and Build (20%)
- Define, build, and modify container images
- Jobs and CronJobs
- Multi-container pod design patterns
- Utilize persistent and ephemeral volumes

### Domain 2: Application Deployment (20%)
- Deployments and rolling updates/rollbacks
- Use Helm package manager
- Use Kustomize
- Understand deployment strategies (blue/green, canary)

### Domain 3: Application Observability and Maintenance (15%)
- Understand API deprecations
- Implement probes and health checks
- Use built-in CLI tools to monitor applications
- Utilize container logs
- Debug in Kubernetes

### Domain 4: Application Environment, Configuration and Security (25%)
- Discover and use CRDs
- Use ConfigMaps and Secrets
- Understand ServiceAccounts
- Understand application resource requirements
- Create and use SecurityContexts

### Domain 5: Services and Networking (20%)
- Demonstrate understanding of Services and NetworkPolicies
- Expose applications using Services
- Use Ingress rules to expose applications

---

## The Three-Pass Strategy (Same as CKA)

Time is your enemy. The same strategy applies:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CKAD Three-Pass Method                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Pass 1: Quick Wins (40-50 min)                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Create pod/deployment/service (imperative commands)   │   │
│  │ • Add labels, annotations                               │   │
│  │ • Expose a deployment                                   │   │
│  │ • Simple ConfigMap/Secret creation                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Pass 2: Medium Tasks (40-50 min)                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Add probes to pods                                    │   │
│  │ • Create multi-container pods                           │   │
│  │ • Jobs and CronJobs                                     │   │
│  │ • Network policies                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Pass 3: Complex Tasks (20-30 min)                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Debugging failing applications                        │   │
│  │ • Complex multi-container patterns                      │   │
│  │ • Helm charts with values                               │   │
│  │ • Troubleshooting scenarios                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### CKAD-Specific Speed Tips

1. **Master imperative commands for common tasks:**
   ```bash
   # These should be muscle memory
   k run nginx --image=nginx
   k create deploy web --image=nginx --replicas=3
   k expose deploy web --port=80 --target-port=8080
   k create job backup --image=busybox -- /bin/sh -c "echo done"
   k create cronjob cleanup --image=busybox --schedule="*/5 * * * *" -- /bin/sh -c "echo cleanup"
   ```

2. **Know the --dry-run pattern for YAML generation:**
   ```bash
   k run nginx --image=nginx --dry-run=client -o yaml > pod.yaml
   ```

3. **Memorize probe syntax—you'll add them repeatedly:**
   ```yaml
   livenessProbe:
     httpGet:
       path: /healthz
       port: 8080
     initialDelaySeconds: 5
     periodSeconds: 10
   ```

4. **Practice multi-container pod patterns until they're automatic**

---

## What You'll Learn in This Curriculum

### Part 0: Environment Setup (This Part)
- CKAD overview and exam strategy
- Developer workflow optimization

### Part 1: Application Design and Build (20%)
- Container images
- Jobs and CronJobs (developer perspective)
- Multi-container pod patterns (sidecar, init, ambassador)
- Volumes for developers

### Part 2: Application Deployment (20%)
- Deployments deep dive
- Helm for developers
- Kustomize for developers
- Deployment strategies

### Part 3: Application Observability and Maintenance (15%)
- Probes (liveness, readiness, startup)
- Container logging
- Debugging applications
- API deprecations

### Part 4: Application Environment, Configuration and Security (25%)
- ConfigMaps and Secrets (advanced patterns)
- ServiceAccounts for applications
- Resource management
- SecurityContexts
- Working with CRDs

### Part 5: Services and Networking (20%)
- Service types and patterns
- Ingress
- NetworkPolicies for applications

### Part 6: Mock Exams
- Timed practice scenarios
- Speed drills

---

## Did You Know?

- **CKAD was the first Kubernetes certification** (launched 2017), followed by CKA later that year. It was designed specifically for developers who deploy to Kubernetes but don't manage clusters.

- **The CKAD pass rate is slightly higher than CKA** because developers often find the hands-on format more intuitive—it mirrors their daily work of creating and debugging applications.

- **Multi-container pods are a CKAD signature topic.** While CKA mentions them, CKAD expects you to implement sidecar, init, and ambassador patterns from memory. You'll see at least 2-3 questions requiring this skill.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Focusing too much on cluster admin | CKAD tests app dev, not cluster setup | Review domain weights above |
| Ignoring init containers | They appear in ~15% of questions | Practice until automatic |
| Not knowing probe syntax | You'll add probes to multiple pods | Memorize the YAML structure |
| Skipping Jobs/CronJobs | They're weighted heavily | Practice all Job patterns |
| Only using `kubectl apply` | Imperative commands save time | Learn `kubectl create/run` |

---

## Quick Reference: CKAD vs CKA Commands

Commands you'll use **more** in CKAD:

```bash
# Jobs and CronJobs
k create job myjob --image=busybox -- echo "hello"
k create cronjob mycron --schedule="* * * * *" --image=busybox -- date

# Generate multi-container pod YAML
k run multi --image=nginx --dry-run=client -o yaml > multi.yaml
# Then edit to add sidecar

# Debugging
k logs pod-name -c container-name
k exec -it pod-name -c container-name -- sh
k debug pod-name --image=busybox --target=container-name

# Quick testing
k run test --image=busybox --rm -it --restart=Never -- wget -qO- http://service
```

---

## Quiz

1. **What percentage of the CKAD exam is dedicated to "Application Environment, Configuration and Security"?**
   <details>
   <summary>Answer</summary>
   25% - the largest domain. This includes ConfigMaps, Secrets, ServiceAccounts, resource requirements, and SecurityContexts.
   </details>

2. **Name the three multi-container pod patterns you need to know for CKAD.**
   <details>
   <summary>Answer</summary>
   Sidecar, Init container, and Ambassador. Sidecar runs alongside the main container, Init runs before main containers start, Ambassador handles proxying.
   </details>

3. **What's the key difference in perspective between CKA and CKAD?**
   <details>
   <summary>Answer</summary>
   CKA focuses on cluster administration (ops perspective), while CKAD focuses on application development (developer perspective). Both require hands-on Kubernetes skills but from different viewpoints.
   </details>

4. **Which CKAD topic is NOT part of the CKA exam?**
   <details>
   <summary>Answer</summary>
   API deprecations awareness is CKAD-specific. Understanding how to check for and handle deprecated APIs is an exam topic.
   </details>

---

## Hands-On Exercise

**Task**: Verify you have the CKA fundamentals needed for CKAD.

**Success Criteria**: Complete these tasks in under 5 minutes total:

```bash
# 1. Create a deployment with 3 replicas
k create deploy ckad-test --image=nginx --replicas=3

# 2. Expose it as a ClusterIP service
k expose deploy ckad-test --port=80

# 3. Create a ConfigMap
k create configmap app-config --from-literal=env=production

# 4. Create a Secret
k create secret generic app-secret --from-literal=password=secret123

# 5. Verify everything
k get deploy,svc,cm,secret | grep ckad
```

If you struggled with any of these, review the relevant CKA modules before continuing.

**Cleanup:**
```bash
k delete deploy ckad-test
k delete svc ckad-test
k delete cm app-config
k delete secret app-secret
```

---

## Practice Drills

### Drill 1: Imperative Speed Test (Target: 3 minutes)

Create the following resources using only imperative commands (no YAML files):

```bash
# 1. Pod named 'web' with nginx image
k run web --image=nginx

# 2. Deployment named 'api' with 2 replicas of httpd
k create deploy api --image=httpd --replicas=2

# 3. Service exposing the api deployment on port 8080
k expose deploy api --port=8080 --target-port=80

# 4. Job named 'backup' that runs busybox and echoes "done"
k create job backup --image=busybox -- echo "done"

# 5. CronJob named 'hourly' running every hour
k create cronjob hourly --image=busybox --schedule="0 * * * *" -- date

# Verify
k get pod,deploy,svc,job,cronjob

# Cleanup
k delete pod web
k delete deploy api
k delete svc api
k delete job backup
k delete cronjob hourly
```

### Drill 2: YAML Generation (Target: 2 minutes)

Generate YAML templates using --dry-run:

```bash
# Generate pod YAML
k run nginx --image=nginx --dry-run=client -o yaml > /tmp/pod.yaml

# Generate deployment YAML
k create deploy web --image=nginx --dry-run=client -o yaml > /tmp/deploy.yaml

# Generate service YAML
k create svc clusterip mysvc --tcp=80:80 --dry-run=client -o yaml > /tmp/svc.yaml

# Verify files exist and are valid
cat /tmp/pod.yaml | head -10
cat /tmp/deploy.yaml | head -10
```

### Drill 3: Context Switching (Target: 2 minutes)

The CKAD exam uses multiple cluster contexts. Practice switching:

```bash
# List available contexts
k config get-contexts

# Switch context (use your actual context names)
k config use-context kind-kind

# Verify current context
k config current-context

# Quick shortcut: set namespace for context
k config set-context --current --namespace=default
```

### Drill 4: Probe Syntax Memorization (Target: 3 minutes)

Write probe YAML from memory—you'll need this repeatedly:

```bash
# Create a pod YAML with all three probe types
cat << 'EOF' > /tmp/probed-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: probed-app
spec:
  containers:
  - name: app
    image: nginx
    ports:
    - containerPort: 80
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 3
      periodSeconds: 5
    startupProbe:
      httpGet:
        path: /
        port: 80
      failureThreshold: 30
      periodSeconds: 10
EOF

# Apply and verify
k apply -f /tmp/probed-pod.yaml
k describe pod probed-app | grep -A5 "Liveness\|Readiness\|Startup"

# Cleanup
k delete pod probed-app
```

### Drill 5: Multi-Container Pattern Recognition (Target: 2 minutes)

Identify which pattern each scenario requires:

```
Scenario 1: Download config before app starts
Answer: Init container

Scenario 2: Ship logs to Elasticsearch alongside main app
Answer: Sidecar

Scenario 3: Wait for database to be ready
Answer: Init container

Scenario 4: Proxy database connections through localhost
Answer: Ambassador

Scenario 5: Monitor and reload config on change
Answer: Sidecar
```

### Drill 6: Domain Weight Recall (Target: 1 minute)

Without looking, write down the five CKAD domains and their weights:

```
1. Application Design and Build - 20%
2. Application Deployment - 20%
3. Application Observability and Maintenance - 15%
4. Application Environment, Configuration and Security - 25%
5. Services and Networking - 20%
```

Verify your answers match the domain breakdown above. This helps you prioritize study time.

---

## Next Module

[Module 0.2: Developer Workflow](../module-0.2-developer-workflow/) - Optimize your kubectl patterns for CKAD speed.
