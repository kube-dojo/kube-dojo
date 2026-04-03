---
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

1. **Create** NetworkPolicies that block pod access to cloud metadata endpoints
2. **Audit** cluster workloads for metadata service exposure risks
3. **Implement** IMDS v2 enforcement and metadata service restrictions on cloud providers
4. **Trace** privilege escalation paths from metadata credentials to cloud resource access

---

## Why This Module Matters

Cloud provider metadata services (like AWS's 169.254.169.254) expose sensitive information: IAM credentials, instance identity, and configuration data. A compromised pod can query this endpoint and potentially escalate privileges or access cloud resources.

This is a favorite attack vector. The 2019 Capital One breach exploited exactly this vulnerability.

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
| AWS | 169.254.169.254 | /latest/meta-data/iam/security-credentials/ |
| GCP | 169.254.169.254 | /computeMetadata/v1/ |
| Azure | 169.254.169.254 | /metadata/identity/oauth2/token |
| DigitalOcean | 169.254.169.254 | /metadata/v1/ |

All use the same IP: **169.254.169.254** (link-local address)

---

## Protection Method 1: NetworkPolicy

Block egress to the metadata IP using NetworkPolicy:

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

Configure iptables rules on each node to block metadata access:

```bash
# Block metadata access from pods (run on each node)
iptables -A OUTPUT -d 169.254.169.254 -j DROP

# Or more specifically, block from pod network
iptables -I FORWARD -s 10.244.0.0/16 -d 169.254.169.254 -j DROP

# Make persistent (varies by OS)
iptables-save > /etc/iptables/rules.v4
```

### DaemonSet for iptables Rules

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

## Protection Method 3: Cloud Provider Features

### AWS IMDSv2 (Recommended)

AWS Instance Metadata Service v2 requires a session token, making direct pod access harder:

```bash
# IMDSv2 requires PUT request first to get token
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Then use token in subsequent requests
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/
```

Configure nodes to require IMDSv2:

```bash
# AWS CLI to enforce IMDSv2 on instance
aws ec2 modify-instance-metadata-options \
  --instance-id i-1234567890abcdef0 \
  --http-tokens required \
  --http-put-response-hop-limit 1
```

### GCP Metadata Concealment

```bash
# Enable metadata concealment on GKE node pool
gcloud container node-pools update POOL_NAME \
  --cluster=CLUSTER_NAME \
  --workload-metadata=GKE_METADATA
```

### Azure Instance Metadata Service (IMDS)

Azure requires specific headers:

```bash
# Azure IMDS requires Metadata header
curl -H "Metadata:true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01"
```

---

## Testing Metadata Access

### Verify Pod Can't Access Metadata

```bash
# Create test pod
kubectl run test-pod --image=curlimages/curl --rm -it --restart=Never -- \
  curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/

# Expected: Connection timeout or refused
# If you see instance metadata, protection isn't working!
```

### Check NetworkPolicy is Applied

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

```bash
# Create test pod
kubectl run metadata-test --image=curlimages/curl -n production --rm -it --restart=Never -- \
  curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/ || echo "BLOCKED (expected)"
```

### Scenario 3: Allow Specific Pod Access

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

## Defense in Depth

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

- **169.254.0.0/16 is link-local.** It's reserved for local network communication and never routed on the internet. Cloud providers use it for metadata because it's accessible from any instance without routing.

- **Kubernetes itself uses metadata** on cloud providers for node information. Blocking system components from metadata can break cluster functionality.

- **AWS IMDSv2 with hop limit 1** prevents containers from reaching metadata because the request goes through multiple network hops (container → node → metadata service).

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Forgetting DNS with egress policy | Pods can't resolve names | Always allow DNS egress |
| Blocking metadata for kube-system | Breaks cloud integrations | Exempt system namespaces carefully |
| Only using NetworkPolicy | Not all CNIs enforce it | Use multiple protection layers |
| Testing from wrong namespace | Policy not applied there | Test from namespace with policy |
| Blocking entire link-local range | May break other services | Start with just 169.254.169.254/32 |

---

## Quiz

1. **What IP address do cloud metadata services use?**
   <details>
   <summary>Answer</summary>
   169.254.169.254 - This is a link-local address used by AWS, GCP, Azure, and other cloud providers for their instance metadata services.
   </details>

2. **Why is blocking metadata access important for security?**
   <details>
   <summary>Answer</summary>
   The metadata service exposes sensitive information including IAM credentials. A compromised pod can query this endpoint to obtain credentials and access cloud resources, enabling lateral movement and privilege escalation.
   </details>

3. **What Kubernetes resource is used to block egress to the metadata IP?**
   <details>
   <summary>Answer</summary>
   NetworkPolicy with egress rules using ipBlock with except for 169.254.169.254/32.
   </details>

4. **What is AWS IMDSv2 and why does it help?**
   <details>
   <summary>Answer</summary>
   Instance Metadata Service version 2 requires a session token obtained via PUT request before accessing metadata. With hop limit 1, containers can't obtain tokens because their requests traverse multiple hops.
   </details>

---

## Hands-On Exercise

**Task**: Block metadata access and verify protection.

```bash
# Setup namespace
kubectl create namespace metadata-test

# Step 1: Verify metadata is accessible (before protection)
kubectl run check-before --image=curlimages/curl -n metadata-test --rm -it --restart=Never -- \
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
  - to: []
    ports:
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
kubectl run check-after --image=curlimages/curl -n metadata-test --rm -it --restart=Never -- \
  curl -s --connect-timeout 3 http://169.254.169.254/ && echo "ACCESSIBLE" || echo "BLOCKED"

# Step 5: Verify other egress still works
kubectl run check-external --image=curlimages/curl -n metadata-test --rm -it --restart=Never -- \
  curl -s --connect-timeout 3 https://kubernetes.io -o /dev/null -w "%{http_code}" && echo " OK"

# Cleanup
kubectl delete namespace metadata-test
```

**Success criteria**: Metadata IP is blocked but external access works.

---

## Summary

**Metadata Service Risk**:
- Exposes IAM credentials and instance data
- Accessible from any pod by default
- Major attack vector (Capital One breach)

**Protection Methods**:
1. NetworkPolicy blocking 169.254.169.254
2. Cloud provider IMDSv2 enforcement
3. Node-level iptables rules
4. Pod Security (no hostNetwork)

**Best Practices**:
- Apply protection to all workload namespaces
- Remember to allow DNS egress
- Use multiple protection layers
- Test that blocks are effective

**Exam Tips**:
- Know how to write the NetworkPolicy from memory
- Understand ipBlock with except syntax
- Remember DNS is UDP port 53

---

## Next Module

[Module 1.5: GUI Security](../module-1.5-gui-security/) - Securing Kubernetes Dashboard and web UIs.
