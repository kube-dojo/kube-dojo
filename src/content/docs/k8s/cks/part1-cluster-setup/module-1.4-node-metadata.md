---
citations_verified: true
revision_pending: true
title: "Module 1.4: Node Metadata Protection"
slug: k8s/cks/part1-cluster-setup/module-1.4-node-metadata
sidebar:
  order: 4
lab:
  id: cks-1.4-node-metadata
  url: https://killercoda.com/kubedojo/scenario/cks-1.4-node-metadata
  duration: "30 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Cloud-specific security critical skill
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: Module 1.1 (Network Policies), understanding of cloud providers

---

## What You'll Be Able to Do

After completing this module, you will be able to:

That means you should be able to apply concrete controls in a real cluster, verify them under failure conditions, and reason about how metadata access can become a privilege-escalation route when policy is incomplete.

1. **Create** NetworkPolicies that block pod access to cloud metadata endpoints
2. **Audit** cluster workloads for metadata service exposure risks
3. **Implement** IMDS v2 enforcement and metadata service restrictions on cloud providers
4. **Trace** privilege escalation paths from metadata credentials to cloud resource access

---

## Why This Module Matters

Cloud provider metadata services (like AWS's `169.254.169.254`) [expose sensitive information: IAM credentials, instance identity, and configuration data](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html). In a Kubernetes cluster, every pod can usually treat the node network as a bridge into this service, so a single container exploit can turn into cloud-account access if the path is not constrained. Because those credentials can be reused against APIs and storage, metadata access is not just a host-level concern; it is a cross-layer identity and privilege-risk chain that can quickly become an enterprise-impacting incident.

This has become a preferred attack vector in real breaches because many teams enforce pod-level isolation but forget that cloud metadata behaves like another “always-available” service to workloads. The 2019 Capital One breach demonstrated how attackers weaponized this path at scale, using it as an entry to credentials and downstream infrastructure, which is why protecting metadata in Kubernetes must be treated as core security controls, not optional hardening.

---

## The Metadata Attack

```
┌─────────────────────────────────────────────────────────────┐
│              METADATA SERVICE ATTACK VECTOR                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                       │
│  │  Compromised    │                                       │
│  │  Application    │                                       │
│  │     Pod         │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           │ curl http://169.254.169.254/latest/meta-data/  │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              METADATA SERVICE                        │   │
│  │                                                      │   │
│  │  Returns:                                           │   │
│  │  • Instance ID                                      │   │
│  │  • Private IP                                       │   │
│  │  • IAM role credentials                             │   │
│  │  • User data (may contain secrets!)                 │   │
│  │  • VPC configuration                                │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Impact:                                                   │
│  ⚠️  Attacker gets temporary AWS credentials               │
│  ⚠️  Can access S3 buckets, databases, etc.               │
│  ⚠️  Lateral movement through cloud resources             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Metadata Endpoints by Provider

| Cloud Provider | Metadata Endpoint | Credential Path |
|----------------|-------------------|-----------------|
| AWS | 169.254.169.254 | [/latest/meta-data/iam/security-credentials/](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html) |
| GCP | 169.254.169.254 | [/computeMetadata/v1/](https://cloud.google.com/compute/docs/metadata/querying-metadata) |
| Azure | 169.254.169.254 | [/metadata/identity/oauth2/token](https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-service) |
| DigitalOcean | 169.254.169.254 | /metadata/v1/ |

All use the same IP: **169.254.169.254** (link-local address)

That commonality creates both operational simplicity and uniform risk: once a team learns how to protect one cloud metadata pattern, the same threat model applies to most environments. Because attackers can pivot from one provider to another with similar workflows, controls need to be applied consistently across all target clouds, not copied and forgotten.

---

> **Stop and think**: An attacker compromises an application pod and runs `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/`. They get temporary AWS credentials with S3 read access. Trace the full attack path: what can they do next, and how far can they go?

## Protection Method 1: NetworkPolicy

Block egress to the metadata IP using NetworkPolicy as your first defense layer; in practice, this is often the simplest way to express “pods should not talk to cloud control-plane secrets.”

When writing the rule, think of it as narrowing the pod egress surface area, not just adding a deny list. The policy makes intent explicit for every workload and gives you a versioned, reviewable security control that can be tested and rolled back.

```yaml
# Block access to metadata service
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata
  namespace: production
spec:
  podSelector: {}  # All pods in namespace
  policyTypes:
  - Egress
  egress:
  # Allow all EXCEPT metadata
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
```

### Allow DNS with Metadata Block

```yaml
# More complete: block metadata but allow DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-metadata-allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  # Allow DNS
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
  # Allow all other traffic except metadata
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
```

---

## Protection Method 2: iptables on Nodes

Configure iptables rules on each node to block metadata access, and treat these rules as a host-based backstop that catches traffic the CNI policy layer misses:

```bash
# Block metadata access from pods (run on each node)
iptables -A OUTPUT -d 169.254.169.254 -j DROP

# Or more specifically, block from pod network
iptables -I FORWARD -s 10.244.0.0/16 -d 169.254.169.254 -j DROP

# Make persistent (varies by OS)
iptables-save > /etc/iptables/rules.v4
```

### DaemonSet for iptables Rules

This DaemonSet uses `hostNetwork: true` and `NET_ADMIN` privileges so it can modify the node's actual iptables rules rather than the pod's isolated network namespace. That distinction matters because ordinary pods only control their own networking namespace, which means a `iptables` change inside one pod does not automatically become a node-wide enforcement point. Using a DaemonSet is defensive in depth when you need host-level enforcement, but it also expands your blast radius, so you should combine it with strict pod security and operational guardrails.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: metadata-blocker
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: metadata-blocker
  template:
    metadata:
      labels:
        app: metadata-blocker
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: blocker
        image: alpine
        command:
        - /bin/sh
        - -c
        - |
          apk add iptables
          iptables -C FORWARD -d 169.254.169.254 -j DROP 2>/dev/null || \
          iptables -I FORWARD -d 169.254.169.254 -j DROP
          sleep infinity
        securityContext:
          privileged: true
          capabilities:
            add: ["NET_ADMIN"]
      tolerations:
      - operator: "Exists"
```

---

> **What would happen if**: You set `--http-put-response-hop-limit 1` on your EC2 instances with IMDSv2. A pod running with `hostNetwork: true` tries to access the metadata service. Does the hop limit protect you? Why or why not?

## Protection Method 3: Cloud Provider Features

### AWS IMDSv2 (Recommended)

[AWS Instance Metadata Service v2 requires a session token](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html), making direct pod access harder because callers must fetch a token before metadata reads succeed.

This hardens the token exchange path against many simple exfiltration scripts, and in practice it forces an attacker to execute a fuller request sequence rather than a single unauthenticated metadata probe.

IMDSv2 changes the threat model because callers must first fetch a short-lived token, which means generic `curl` probes are no longer enough to retrieve metadata. In practice, this helps block many common container-based attacks, but you still need to reason about hop count and host-network workloads before assuming complete protection.

```bash
# IMDSv2 requires PUT request first to get token
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Then use token in subsequent requests
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/
```

Configure nodes to require IMDSv2 with provider tooling so every instance follows the stricter behavior, and verify each node group setting after upgrades to prevent configuration drift when templates or images change:

```bash
# AWS CLI to enforce IMDSv2 on instance
aws ec2 modify-instance-metadata-options \
  --instance-id i-1234567890abcdef0 \
  --http-tokens required \
  --http-put-response-hop-limit 1
```

### GCP Metadata Concealment

If workloads move across providers, this is your equivalent to IMDS controls on GCP: configure metadata behavior at node-pool level so workloads cannot assume unrestricted metadata exposure by default. In many environments this starts as a “one flag in pool config” change and becomes a reliable baseline safeguard for all new nodes.

```bash
# Enable metadata concealment on GKE node pool
gcloud container node-pools update POOL_NAME \
  --cluster=CLUSTER_NAME \
  --workload-metadata=GKE_METADATA
```

### Azure Instance Metadata Service (IMDS)

Azure requires specific headers, and the endpoint accepts only calls that include those security markers, which is why simple unauthenticated probes often fail even when the IP is reachable.

In a Kubernetes threat model, this means your defenses should still assume a determined attacker may test multiple metadata flavors and chains, because headers can be learned but not always trusted if the pod is already running with privileged network access.

```bash
# Azure IMDS requires Metadata header
curl -H "Metadata:true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01"
```

---

## Testing Metadata Access

### Verify Pod Can't Access Metadata

Use this check early in your validation flow to confirm the policy is active for a test pod in the target namespace. If metadata is blocked, your probe should fail or timeout; that behavior is the expected security signal, not a platform error.

```bash
# Create test pod
kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- \
  curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/

# Expected: Connection timeout or refused
# If you see instance metadata, protection isn't working!
```

### Check NetworkPolicy is Applied

After running the runtime probe, inspect policy objects and pod selectors so you can prove *scope* and *coverage*. The key question is not only whether traffic is blocked, but whether the right namespaces and workloads are actually selected by the rule.

```bash
# List network policies
kubectl get networkpolicies -n production

# Describe specific policy
kubectl describe networkpolicy block-metadata -n production

# Check if pod is selected by policy
kubectl get pod test-pod -n production --show-labels
```

---

## Complete Security Example

The following example pulls together egress policy behavior used in production patterns: allow internal service communication, permit DNS, and explicitly exclude metadata from the broader egress set. This shape is useful because it preserves day-to-day connectivity while keeping the risk-bearing link-local endpoint unreachable.

```yaml
# Apply to every namespace that runs workloads
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-metadata
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  # Allow DNS resolution
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
  # Allow cluster internal communication
  - to:
    - ipBlock:
        cidr: 10.0.0.0/8
  # Allow external but block metadata
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.0.0/16  # Block entire link-local range
```

---

## Real Exam Scenarios

### Scenario 1: Block Metadata Access for Namespace

This is the pattern examiners often probe: can you apply a policy with minimal overreach and still keep behavior predictable. The snippet is intentionally namespace-scoped so you practice control-plane granularity without touching system components.

```bash
# Create NetworkPolicy to block metadata
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-cloud-metadata
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
EOF

# Verify
kubectl get networkpolicy block-cloud-metadata -n production
```

### Scenario 2: Test and Verify Block

Once a policy is in place, always verify with an explicit failure expectation so operators reading your remediation can tell protected and unprotected paths apart. Use an exit-coded check during remediation checks to avoid false-positive “looks fine” interpretations.

```bash
# Create test pod
kubectl run metadata-test --image=curlimages/curl -n production --rm -i --restart=Never -- \
  curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/ || echo "BLOCKED (expected)"
```

### Scenario 3: Allow Specific Pod Access

Not every workload should be blocked; this scenario demonstrates an explicit exception pattern. You can constrain that exception to monitoring or agent pods while still preserving broad protections for untrusted workloads.

```yaml
# Most pods blocked, but monitoring pod needs metadata
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-monitoring-metadata
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: cloud-monitor
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0  # All traffic including metadata
```

---

> **Pause and predict**: You block metadata access for the `production` namespace with a NetworkPolicy. But you don't apply it to `kube-system`. Why might this be intentional, and what risk does it introduce?

## Defense in Depth

Single controls are useful, but defenses fail from edge cases more often than from one missing line of docs. Build in layers: kube-network policy, provider-level metadata posture, node-level enforcement, and runtime least-privilege, then validate each layer independently.

```
┌─────────────────────────────────────────────────────────────┐
│              METADATA PROTECTION LAYERS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: NetworkPolicy                                    │
│  └── Block egress to 169.254.169.254                       │
│                                                             │
│  Layer 2: Cloud Provider IMDSv2                           │
│  └── Require session tokens                                │
│                                                             │
│  Layer 3: Node-level iptables                             │
│  └── Block at network level                                │
│                                                             │
│  Layer 4: Pod Security                                    │
│  └── Restrict host networking                              │
│                                                             │
│  Layer 5: Minimal IAM                                      │
│  └── Node roles with least privilege                       │
│                                                             │
│  Best practice: Use MULTIPLE layers                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **The 2019 Capital One breach** exposed 100 million customer records through SSRF to the metadata service. The attacker obtained IAM credentials and accessed S3 buckets.

- **[169.254.0.0/16 is link-local.](https://www.rfc-editor.org/rfc/rfc3927)** It's reserved for local network communication and never routed on the internet. Cloud providers use it for metadata because it's accessible from any instance without routing, which is why this space is consistently reused across AWS, GCP, and Azure.

- **Kubernetes itself uses metadata** on cloud providers for node information. [Blocking system components from metadata can break cluster functionality](https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata). In practice, that means security design needs namespace and workload scoping, not a blanket policy that accidentally blocks control-plane-dependent services.

- **AWS IMDSv2 with hop limit 1** makes metadata harder to reach from nested network paths, because every additional hop can cause token requests to fail in constrained environments (container → node → metadata service). This can break legitimate paths as well, which is why the value should be paired with pod egress policies and periodic validation.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting DNS with egress policy | Pods can't resolve names | Always allow DNS egress |
| Blocking metadata for kube-system | Breaks cloud integrations | Exempt system namespaces carefully |
| Only using NetworkPolicy | [Not all CNIs enforce it](https://kubernetes.io/docs/concepts/services-networking/network-policies/) | Use multiple protection layers |
| Testing from wrong namespace | Policy not applied there | Test from namespace with policy |
| Blocking entire link-local range | May break other services | Start with just 169.254.169.254/32 |

---

## Quiz

1. **A penetration tester reports they obtained temporary AWS credentials from inside a pod by running `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/node-role`. Using those credentials, they listed all S3 buckets in the account. What is the IP they targeted, and what two layers of defense would have prevented this?**
   <details>
   <summary>Answer</summary>
   The IP 169.254.169.254 is the cloud metadata service link-local address, used by all major cloud providers (AWS, GCP, Azure). Two layers of defense: (1) A NetworkPolicy with egress rules using `ipBlock` with `except: [169.254.169.254/32]` to block pods from reaching the metadata service at the network level. (2) AWS IMDSv2 enforcement with `--http-tokens required` and `--http-put-response-hop-limit 1` -- this requires a session token that containers can't obtain because their requests traverse multiple network hops. Defense in depth means using both.
   </details>

2. **You apply a metadata-blocking NetworkPolicy to the `production` namespace. The next day, the cloud provider's node autoscaler stops working. Investigation reveals a system pod in `kube-system` needs metadata access to function. How do you fix this without compromising production security?**
   <details>
   <summary>Answer</summary>
   Don't apply the metadata-blocking NetworkPolicy to `kube-system` -- system components like cloud controller managers, node autoscalers, and CSI drivers legitimately need metadata access to interact with cloud APIs. Apply metadata blocking only to workload namespaces (`production`, `staging`, etc.) and leave system namespaces unblocked. For additional security on system namespaces, use IMDSv2 enforcement and ensure node IAM roles follow least privilege. This is an intentional trade-off: system components need metadata, application pods don't.
   </details>

3. **Your cluster runs on AWS with IMDSv2 enforced (`--http-tokens required`, `--http-put-response-hop-limit 1`). A security engineer argues that NetworkPolicies for metadata blocking are now redundant. Is she correct?**
   <details>
   <summary>Answer</summary>
   She is partially correct but not entirely. IMDSv2 with hop limit 1 prevents most container-based metadata attacks because pod network traffic traverses multiple hops. However, pods with `hostNetwork: true` share the node's network namespace and can access metadata as if they were the node itself (only 1 hop). Also, IMDSv2 is AWS-specific -- if workloads move to GCP or Azure, you lose that protection. NetworkPolicies provide cloud-agnostic defense and catch edge cases. Best practice is defense in depth: use both IMDSv2 AND NetworkPolicies.
   </details>

4. **You write a NetworkPolicy to block metadata but forget to include a DNS egress rule. Your application pods start failing with "could not resolve host" errors even though they never accessed the metadata service. Explain the connection between metadata blocking and DNS, and write the fix.**
   <details>
   <summary>Answer</summary>
   If you specify `policyTypes: [Egress]` in a NetworkPolicy, all egress traffic not explicitly allowed is denied. This includes DNS queries to kube-dns (UDP port 53). Even though DNS has nothing to do with metadata, the egress policy blocks ALL traffic except what you whitelist. The fix is to add a DNS egress rule: allow UDP/TCP port 53 to pods labeled `k8s-app: kube-dns` in any namespace. A complete metadata-blocking policy needs both the DNS allow rule AND the `ipBlock` with `except: [169.254.169.254/32]` for all other traffic.
   </details>

---

## Hands-On Exercise

**Task**: Block metadata access and verify protection. Treat it as a controlled exercise: first observe current behavior, then apply your policy changes, then run all post-change probes so the security state is reproducible for future audits.

```bash
# Setup namespace
kubectl create namespace metadata-test

# Step 1: Verify metadata is accessible (before protection)
kubectl run check-before --image=curlimages/curl -n metadata-test --rm -i --restart=Never -- \
  curl -s --connect-timeout 3 http://169.254.169.254/ && echo "ACCESSIBLE" || echo "BLOCKED"

# Note: In non-cloud environments, you'll see "BLOCKED" already

# Step 2: Apply metadata blocking NetworkPolicy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata
  namespace: metadata-test
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  # Allow DNS
  - ports:
    - port: 53
      protocol: UDP
  # Allow all except metadata
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
EOF

# Step 3: Verify policy exists
kubectl get networkpolicy -n metadata-test
kubectl describe networkpolicy block-metadata -n metadata-test

# Step 4: Test metadata is blocked
kubectl run check-after --image=curlimages/curl -n metadata-test --rm -i --restart=Never -- \
  curl -s --connect-timeout 3 http://169.254.169.254/ && echo "ACCESSIBLE" || echo "BLOCKED"

# Step 5: Verify other egress still works
kubectl run check-external --image=curlimages/curl -n metadata-test --rm -i --restart=Never -- \
  curl -s --connect-timeout 3 https://kubernetes.io -o /dev/null -w "%{http_code}" && echo " OK"

# Cleanup
kubectl delete namespace metadata-test
```

**Success criteria**: Metadata IP is blocked but external access works. A successful outcome is a clear pass/fail signal: metadata endpoints are unreachable from the test workload, while general outbound traffic still succeeds.

---

## Summary

**Metadata Service Risk**: Metadata endpoints can leak IAM credentials, node identity, and configuration context; when left open, they are a direct bridge from pod compromise to cloud-resource actions. The module’s attack examples are a reminder that this is not a hypothetical risk—metadata abuse frequently appears in real breach narratives.

**Protection Methods**: This module combines four defensive layers: NetworkPolicy egress restrictions, cloud-provider IMDS enforcement, host-level iptables enforcement via Kubernetes-native workflows, and pod architecture choices such as avoiding unnecessary `hostNetwork` privileges.

**Best Practices**: Apply defenses to workload namespaces by default, keep DNS egress explicitly allowed, and use layered controls so one control failure does not expose metadata. Regularly run the validation probes after drift events, because control posture is only reliable when proven in repeatable checks.

These points are only safe when backed by repeatable checks: if you cannot observe blocked/allowed behavior on demand, you should treat the control as incomplete even if the intent is documented.

**Exam Tips**: Focus on writing NetworkPolicies cleanly from memory, including `ipBlock` exceptions and DNS allowances, and remember that metadata attack prevention is a defense-in-depth objective, not a single toggle.

---

## Next Module

[Module 1.5: GUI Security](../module-1.5-gui-security/) - Securing Kubernetes Dashboard and web UIs.

This transition is intentional: once you have metadata and workload egress under control, you can apply the same threat-model discipline to user-facing administrative surfaces.

## Sources

- [docs.aws.amazon.com: ec2 instance metadata.html](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html) — AWS EC2 documentation directly describes instance metadata categories, including IAM role credentials and user data.
- [cloud.google.com: querying metadata](https://cloud.google.com/compute/docs/metadata/querying-metadata) — Google Cloud's Compute Engine metadata documentation directly names both the IP and the /computeMetadata/v1 endpoint.
- [learn.microsoft.com: instance metadata service](https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-service) — Microsoft Learn directly documents the IMDS IP, the metadata root, and the required Metadata header for requests.
- [rfc-editor.org: rfc3927](https://www.rfc-editor.org/rfc/rfc3927) — RFC 3927 is the authoritative standard for IPv4 link-local addressing and forwarding behavior.
- [docs.aws.amazon.com: configuring instance metadata options.html](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html) — AWS documentation directly explains IMDSv2 token requirements and the instance metadata option that enforces IMDSv2-only access.
- [cloud.google.com: protecting cluster metadata](https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata) — Google's GKE documentation states that GKE uses instance metadata to configure node VMs and documents protected-vs-allowed metadata access behavior.
- [kubernetes.io: network policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/) — Kubernetes documentation states that NetworkPolicies are implemented by the network plugin and have no effect without a controller that supports enforcement.
- [AWS IMDSv2 Overview](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) — Explains how IMDSv2 works, how tokens are retrieved, and how hop limits affect access.
