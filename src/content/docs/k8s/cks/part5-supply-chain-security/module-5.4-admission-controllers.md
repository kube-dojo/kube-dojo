---
title: "Module 5.4: Admission Controllers"
slug: k8s/cks/part5-supply-chain-security/module-5.4-admission-controllers
sidebar:
  order: 4
lab:
  id: cks-5.4-admission-controllers
  url: https://killercoda.com/kubedojo/scenario/cks-5.4-admission-controllers
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical CKS topic
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 5.3 (Static Analysis), API server basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** validating and mutating admission webhooks for custom security enforcement
2. **Implement** ImagePolicyWebhook to restrict which container registries are allowed
3. **Audit** enabled admission controllers and their impact on cluster security posture
4. **Debug** admission controller rejections by interpreting webhook response errors

---

## Why This Module Matters

Imagine a highly exclusive nightclub or airport security. The authentication system checks if you have a valid ID. The authorization system checks if you have a boarding pass or are on the VIP list. But the **admission controller** is the bouncer or security screener at the door who checks if you're carrying a weapon, wearing forbidden items, or otherwise violating policy. Even if you have a valid ID and are on the list, the admission controller can still reject you, force you to check your coat (mutate), or let you pass (validate).

Admission controllers are gatekeepers that intercept API requests before objects are persisted. They can validate, mutate, or reject requests based on custom logic. Understanding how to enable and configure admission controllers is essential for cluster security.

CKS tests admission controller configuration and usage.

---

## Admission Controller Flow

```
┌─────────────────────────────────────────────────────────────┐
│              ADMISSION CONTROLLER PIPELINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl create/apply                                       │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Authentication (who is this?)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Authorization (can they do this?)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Mutating Admission (modify the request)            │   │
│  │  ├── MutatingAdmissionWebhook                       │   │
│  │  ├── DefaultStorageClass                            │   │
│  │  └── PodPreset (deprecated)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Validating Admission (approve/deny)                │   │
│  │  ├── ValidatingAdmissionWebhook                     │   │
│  │  ├── PodSecurity (PSA)                              │   │
│  │  └── ResourceQuota                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  etcd (persist object)                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **Stop and think**: Every pod creation, update, and deletion passes through admission controllers. If you add a ValidatingAdmissionWebhook that validates images against a policy server, and that server goes down, what happens to ALL pod operations in the cluster? What's the critical `failurePolicy` setting?

## Built-in Admission Controllers

### Security-Critical Controllers

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY ADMISSION CONTROLLERS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PodSecurity (Kubernetes 1.25+)                            │
│  └── Enforces Pod Security Standards                       │
│      Replaces PodSecurityPolicy                            │
│                                                             │
│  NodeRestriction                                           │
│  └── Limits what kubelets can modify                       │
│      Prevents compromised nodes from affecting others      │
│                                                             │
│  AlwaysPullImages                                          │
│  └── Forces image pull on every pod start                  │
│      Prevents using cached malicious images                │
│                                                             │
│  ImagePolicyWebhook                                        │
│  └── External image verification                           │
│      Can block unsigned or vulnerable images               │
│                                                             │
│  DenyServiceExternalIPs                                    │
│  └── Blocks Service externalIPs                            │
│      Prevents CVE-2020-8554 attacks                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Check Enabled Controllers

```bash
# On kubeadm clusters
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep enable-admission-plugins

# Or via API
kubectl get pod kube-apiserver-<node> -n kube-system -o yaml | \
  grep enable-admission-plugins
```

### Enable Additional Controllers

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
spec:
  containers:
  - command:
    - kube-apiserver
    - --enable-admission-plugins=NodeRestriction,PodSecurity,AlwaysPullImages
    # Other flags...
```

---

## ValidatingAdmissionWebhook

ValidatingAdmissionWebhooks call external services to validate requests.

### Webhook Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              VALIDATING WEBHOOK FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl apply -f pod.yaml                                 │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Kubernetes API Server                     │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         │  AdmissionReview request (JSON)                  │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Webhook Service (HTTPS)                     │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Validate request                           │    │   │
│  │  │  • Check image signatures                   │    │   │
│  │  │  • Verify security context                  │    │   │
│  │  │  • Custom business logic                    │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         │  AdmissionReview response                        │
│         │  { "allowed": true/false, "status": {...} }     │
│         ▼                                                   │
│  API Server allows or denies request                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Creating a ValidatingWebhookConfiguration

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-validator
webhooks:
- name: pod-validator.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  clientConfig:
    service:
      name: pod-validator
      namespace: security
      path: /validate
    caBundle: <base64-encoded-ca-cert>
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE", "UPDATE"]
    resources: ["pods"]
  failurePolicy: Fail  # Fail or Ignore
  matchPolicy: Equivalent
  namespaceSelector:
    matchLabels:
      validate-pods: "true"
```

### Key Configuration Options

```yaml
# failurePolicy: What happens if webhook is unavailable
failurePolicy: Fail    # Reject request (secure but may block cluster)
failurePolicy: Ignore  # Allow request (less secure but more available)

# sideEffects: Does webhook have side effects?
sideEffects: None      # Safe to call multiple times
sideEffects: Unknown   # May have side effects

# timeoutSeconds: How long to wait for response
timeoutSeconds: 10     # Default is 10 seconds

# namespaceSelector: Which namespaces to apply to
namespaceSelector:
  matchLabels:
    env: production

# objectSelector: Which objects to validate
objectSelector:
  matchLabels:
    validate: "true"
```

---

> **Stop and think**: A MutatingAdmissionWebhook silently injects a sidecar container into every pod. An attacker compromises the webhook service and changes the sidecar image to a malicious one. Every new pod in the cluster now contains the attacker's container. How do you protect against this?

## ImagePolicyWebhook

ImagePolicyWebhook validates image names before pods are created.

### Enable ImagePolicyWebhook

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --enable-admission-plugins=ImagePolicyWebhook
    - --admission-control-config-file=/etc/kubernetes/admission/config.yaml
    volumeMounts:
    - mountPath: /etc/kubernetes/admission
      name: admission-config
      readOnly: true
  volumes:
  - hostPath:
      path: /etc/kubernetes/admission
      type: DirectoryOrCreate
    name: admission-config
```

### ImagePolicyWebhook Configuration

```yaml
# /etc/kubernetes/admission/config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: ImagePolicyWebhook
  configuration:
    imagePolicy:
      kubeConfigFile: /etc/kubernetes/admission/kubeconfig
      allowTTL: 50
      denyTTL: 50
      retryBackoff: 500
      defaultAllow: false  # IMPORTANT: Deny by default
```

### kubeconfig for ImagePolicyWebhook

```yaml
# /etc/kubernetes/admission/kubeconfig
apiVersion: v1
kind: Config
clusters:
- name: image-checker
  cluster:
    certificate-authority: /etc/kubernetes/admission/ca.crt
    server: https://image-checker.security.svc:443/check
contexts:
- name: image-checker
  context:
    cluster: image-checker
current-context: image-checker
```

### ImageReview Request/Response

```json
// Request sent to webhook
{
  "apiVersion": "imagepolicy.k8s.io/v1alpha1",
  "kind": "ImageReview",
  "spec": {
    "containers": [
      {
        "image": "nginx:1.25"
      }
    ],
    "namespace": "production"
  }
}

// Response from webhook
{
  "apiVersion": "imagepolicy.k8s.io/v1alpha1",
  "kind": "ImageReview",
  "status": {
    "allowed": true,
    "reason": "Image signed and scanned"
  }
}
```

---

## MutatingAdmissionWebhook

MutatingWebhooks modify requests before validation.

### Common Use Cases

```
┌─────────────────────────────────────────────────────────────┐
│              MUTATING WEBHOOK USE CASES                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Inject sidecars                                           │
│  └── Add logging, monitoring, or security containers       │
│      (Istio, Linkerd service mesh)                         │
│                                                             │
│  Add default labels/annotations                            │
│  └── Automatically add team, cost-center labels            │
│                                                             │
│  Set default security context                              │
│  └── Add runAsNonRoot: true if not specified              │
│                                                             │
│  Add imagePullSecrets                                      │
│  └── Inject registry credentials automatically             │
│                                                             │
│  Modify resource requests                                  │
│  └── Set default memory/CPU if not specified              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### MutatingWebhookConfiguration

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: pod-mutator
webhooks:
- name: pod-mutator.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  clientConfig:
    service:
      name: pod-mutator
      namespace: security
      path: /mutate
    caBundle: <base64-encoded-ca-cert>
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
  reinvocationPolicy: Never  # or IfNeeded
```

---

> **Pause and predict**: You configure an ImagePolicyWebhook with `defaultAllow: false`. The webhook service crashes. A developer tries to deploy a pod. What happens -- does the pod get created, or is it blocked?

## Debugging Webhook Failures

When a validating or mutating webhook blocks a request, or the webhook service itself is unhealthy, it can cause confusing cluster behavior. Here is how to investigate and debug these failures.

### 1. Direct API Rejections
When you create a Pod directly via `kubectl run`, the API server will return the webhook's rejection message or timeout error immediately in your terminal.
```bash
$ kubectl run nginx --image=nginx
Error from server (InternalError): Internal error occurred: failed calling webhook "validate.example.com": failed to call webhook: context deadline exceeded
```

### 2. Silent Deployment Failures
If you create a Deployment, the Deployment object is created successfully (because the webhook is only targeting `pods`), but no Pods will appear. The ReplicaSet controller receives the webhook rejection and records it as an event.
```bash
# Check why a Deployment has 0 available replicas
kubectl describe replicaset <deployment-name>
# Look under 'Events:' for webhook rejection messages
```

### 3. API Server Logs
If the webhook service is crashing or returning invalid JSON, the API server logs will contain the detailed communication errors.
```bash
# On control plane node or using kubectl (if you have access)
kubectl logs -n kube-system -l component=kube-apiserver | grep -i webhook
```

### 4. Check Webhook Service Health
Ensure the service backing the webhook configuration has healthy endpoints and the pods are running.
```bash
kubectl get endpoints -n <webhook-namespace> <webhook-service-name>
kubectl logs -n <webhook-namespace> -l app=<webhook-app>
```

---

## Real Exam Scenarios

### Scenario 1: Enable AlwaysPullImages

```bash
# Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Find or add the --enable-admission-plugins flag
# Add AlwaysPullImages to the list:
# --enable-admission-plugins=NodeRestriction,PodSecurity,AlwaysPullImages

# Wait for API server to restart
kubectl get nodes

# Test: Pods should always pull images
kubectl run test --image=nginx
kubectl get pod test -o yaml | grep imagePullPolicy
# Should show "Always"
```

### Scenario 2: Create ValidatingWebhookConfiguration

```bash
# Create webhook configuration that blocks pods without labels
cat <<EOF | kubectl apply -f -
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: require-labels
webhooks:
- name: require-labels.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
  clientConfig:
    service:
      name: label-validator
      namespace: default
      path: /validate
    caBundle: LS0tLS1CRUdJTi...  # Base64 CA cert
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
  namespaceSelector:
    matchLabels:
      require-labels: "true"
EOF
```

### Scenario 3: Configure ImagePolicyWebhook

```bash
# Create admission config directory
sudo mkdir -p /etc/kubernetes/admission

# Create admission configuration
sudo tee /etc/kubernetes/admission/admission-config.yaml << 'EOF'
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: ImagePolicyWebhook
  configuration:
    imagePolicy:
      kubeConfigFile: /etc/kubernetes/admission/kubeconfig
      allowTTL: 50
      denyTTL: 50
      retryBackoff: 500
      defaultAllow: false
EOF

# Create kubeconfig for webhook
sudo tee /etc/kubernetes/admission/kubeconfig << 'EOF'
apiVersion: v1
kind: Config
clusters:
- name: image-policy
  cluster:
    certificate-authority: /etc/kubernetes/admission/ca.crt
    server: https://image-policy.security.svc:443/check
contexts:
- name: image-policy
  context:
    cluster: image-policy
current-context: image-policy
EOF

# Update API server manifest to enable ImagePolicyWebhook
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# Add: --enable-admission-plugins=...,ImagePolicyWebhook
# Add: --admission-control-config-file=/etc/kubernetes/admission/admission-config.yaml
# Add volume mount for /etc/kubernetes/admission
```

---

## Admission Controller Security Recommendations

```
┌─────────────────────────────────────────────────────────────┐
│              ADMISSION CONTROLLER RECOMMENDATIONS           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENABLE (Security-critical):                               │
│  ├── NodeRestriction (always)                              │
│  ├── PodSecurity (Kubernetes 1.25+)                       │
│  ├── AlwaysPullImages (multi-tenant clusters)             │
│  └── DenyServiceExternalIPs (if not needed)               │
│                                                             │
│  CONSIDER (Based on requirements):                         │
│  ├── ImagePolicyWebhook (image validation)                │
│  ├── ValidatingAdmissionWebhook (custom policies)         │
│  └── MutatingAdmissionWebhook (default values)            │
│                                                             │
│  DISABLED BY DEFAULT (Enable carefully):                  │
│  ├── AlwaysDeny (testing only)                            │
│  └── EventRateLimit (can break cluster)                   │
│                                                             │
│  DEPRECATED:                                               │
│  └── PodSecurityPolicy (removed 1.25)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Admission controllers run in order**: Mutating webhooks run first, then validating webhooks. This allows mutations to be validated.

- **failurePolicy is critical**: Setting it to `Fail` is more secure but can cause cluster-wide outages if the webhook service is down.

- **NodeRestriction prevents node takeover**: It limits kubelets to only modify pods running on their node and their own Node object.

- **AlwaysPullImages has performance impact**: Every pod start requires an image pull, which increases latency and registry load.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| failurePolicy: Ignore | Bypasses security checks | Use Fail with high availability |
| No namespaceSelector | Applies to all namespaces | Exclude kube-system |
| Webhook timeout too short | False failures | Set 10-30 seconds |
| Not enabling NodeRestriction | Compromised node attacks | Always enable |
| defaultAllow: true | Unsigned images allowed | Set to false |

---

## Quiz

1. **Your service mesh uses a MutatingAdmissionWebhook to inject sidecar proxies into every pod. A security audit reveals the webhook service itself runs with no NetworkPolicy and its TLS certificate expired 2 months ago. The auditor calls this "the keys to the kingdom." Why is a compromised mutating webhook so dangerous?**
   <details>
   <summary>Answer</summary>
   A MutatingAdmissionWebhook can modify any pod creation request -- it runs before validation. A compromised webhook could inject malicious sidecar containers (cryptominers, reverse shells), modify environment variables to steal secrets, change image references to backdoored versions, or add `privileged: true` to security contexts. Since it processes every pod in matched namespaces, the blast radius is the entire cluster. Protection: secure the webhook with mTLS, apply strict NetworkPolicies, use RBAC to restrict who can modify the webhook configuration, and add a ValidatingAdmissionWebhook that runs after mutation to verify pods haven't been tampered with.
   </details>

2. **You deploy a ValidatingAdmissionWebhook with `failurePolicy: Fail` that checks all images against an allowlist. The webhook service pod gets OOMKilled during a traffic spike. Suddenly, no pods can be created or updated anywhere in the cluster -- including the webhook pod itself trying to restart. How do you recover from this deadlock?**
   <details>
   <summary>Answer</summary>
   This is a classic webhook deadlock. Recovery: (1) Delete the ValidatingWebhookConfiguration with `kubectl delete validatingwebhookconfiguration <name>` -- this removes the admission check and unblocks pod creation. (2) Fix the webhook service (increase memory limits, add resource requests). (3) Re-apply the webhook configuration with safeguards. Prevention: always exclude `kube-system` and the webhook's own namespace from the webhook rules using `namespaceSelector`. Set `timeoutSeconds` to a low value (5s). Consider `failurePolicy: Ignore` for non-critical webhooks. For critical security webhooks, use `Fail` but ensure high availability (multiple replicas, PodDisruptionBudget).
   </details>

3. **During a CKS exam, you're asked to configure an ImagePolicyWebhook that blocks images not from `registry.internal.io`. You set `defaultAllow: false` and configure the admission controller. Pods with internal images work, but system pods in `kube-system` that use `registry.k8s.io` images stop being created. What did you miss?**
   <details>
   <summary>Answer</summary>
   ImagePolicyWebhook applies to all image pull requests unless specifically exempted. System images from `registry.k8s.io` are now blocked because they're not from your internal registry. Fix: the webhook's image review logic should allowlist both `registry.internal.io` AND `registry.k8s.io` (and any other system image registries your cluster needs). Alternatively, configure the admission controller configuration to exempt the `kube-system` namespace. With `defaultAllow: false`, everything not explicitly allowed is denied -- including system components. Always test admission policies against system namespaces before enforcement.
   </details>

4. **Your cluster has both a MutatingAdmissionWebhook (injecting resource limits) and a ValidatingAdmissionWebhook (checking security contexts). A pod is submitted without resource limits and without `runAsNonRoot`. In what order do the webhooks process it, and what's the final result?**
   <details>
   <summary>Answer</summary>
   Order: Mutating webhooks run first, then Validating webhooks. The mutating webhook adds resource limits to the pod spec. Then the validating webhook checks the (now-mutated) pod for security contexts. The pod is rejected because it still lacks `runAsNonRoot` -- the mutating webhook only added limits, not security contexts. The developer must add the security context. This ordering is important: validation sees the final mutated version of the request, so mutating webhooks can fix some issues before validation. But validation catches anything that mutation didn't address. They work as complementary layers.
   </details>

---

## Hands-On Exercise

**Task**: Deploy a validating webhook configuration and observe how a failure impacts cluster operations. 

```bash
# Step 1: Create a namespace for our test
kubectl create namespace webhook-test
kubectl label namespace webhook-test enforce-policy=true

# Step 2: Deploy a "broken" ValidatingWebhookConfiguration
# This webhook requires a service that doesn't exist, simulating a downed security tool.
cat <<EOF | kubectl apply -f -
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: broken-bouncer
webhooks:
- name: bouncer.security.local
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
  timeoutSeconds: 3
  clientConfig:
    service:
      name: missing-service
      namespace: default
      path: /validate
    caBundle: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCg== # Dummy CA
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
  namespaceSelector:
    matchLabels:
      enforce-policy: "true"
EOF

# Step 3: Attempt to create a pod in the labeled namespace
# This will FAIL because the webhook service is unreachable and failurePolicy is Fail.
kubectl run test-pod --image=nginx -n webhook-test

# Step 4: Debug the failure
# The direct pod creation shows the error immediately. Let's see how Deployments fail silently.
kubectl create deployment test-deploy --image=nginx -n webhook-test
kubectl get pods -n webhook-test
# No pods are created! The Deployment controller succeeded, but the ReplicaSet failed.

# Step 5: Check the ReplicaSet events to find the webhook error
RS_NAME=$(kubectl get replicaset -n webhook-test -o jsonpath='{.items[0].metadata.name}')
kubectl describe replicaset $RS_NAME -n webhook-test | grep -i webhook

# Step 6: Fix the cluster by removing the broken webhook
kubectl delete validatingwebhookconfiguration broken-bouncer
kubectl get pods -n webhook-test -w
# The deployment will now successfully create the pod!

# Cleanup
kubectl delete namespace webhook-test
```

**Success criteria**: Understand how to configure a webhook and debug deployment failures when a webhook blocks pod creation.

---

## Summary

**Admission Controller Types**:
- Built-in controllers (enable via API server flag)
- ValidatingAdmissionWebhooks (external validation)
- MutatingAdmissionWebhooks (external mutation)

**Key Security Controllers**:
- NodeRestriction (always enable)
- PodSecurity (PSA)
- AlwaysPullImages (multi-tenant)
- ImagePolicyWebhook (image validation)

**Webhook Configuration**:
- failurePolicy: Fail vs Ignore
- namespaceSelector for scoping
- sideEffects declaration
- timeout settings

**Exam Tips**:
- Know how to enable controllers in API server
- Understand webhook configuration YAML
- Remember failurePolicy implications

---

## Part 5 Complete!

You've finished **Supply Chain Security** (20% of CKS). You now understand:
- Container image security best practices
- Image scanning with Trivy
- Static analysis with kubesec and OPA
- Admission controllers and webhooks

**Next Part**: [Part 6: Monitoring, Logging & Runtime Security](../part6-runtime-security/module-6.1-audit-logging/) - Detecting and responding to security incidents.