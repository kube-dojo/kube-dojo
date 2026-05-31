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

1. **Create** NetworkPolicies that block pod access to cloud metadata endpoints
2. **Audit** cluster workloads for metadata service exposure risks
3. **Implement** IMDS v2 enforcement and metadata service restrictions on cloud providers
4. **Trace** privilege escalation paths from metadata credentials to cloud resource access

That means you should be able to apply concrete controls in a real cluster, verify them under failure conditions, and reason about how metadata access can become a privilege-escalation route when policy is incomplete.

You should also be able to explain the limits of each control. A correct answer on this topic is not just "block `169.254.169.254`." A correct answer names the workload namespace, the CNI enforcement requirement, the provider feature that reduces credential exposure, and the verification command that proves the chosen pod can no longer reach the metadata service.

For the CKS, this is a practical skill rather than a memorized cloud trivia topic. You may be asked to write the policy, but the scenario usually tests whether you understand why the policy works and where it stops. The best answers combine fast YAML execution with a short explanation of enforcement, verification, and identity scope.

---

## Why This Module Matters

Cloud provider metadata services, such as AWS EC2 instance metadata at `169.254.169.254`, [expose node identity, configuration details, and IAM role credentials](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html). In a Kubernetes cluster, an ordinary application pod often has a route through the node network to that link-local endpoint unless you block it. That means a web bug, SSRF flaw, shell escape, or vulnerable sidecar can become a cloud-identity problem rather than staying inside the original container.

This module matters because metadata access cuts across boundaries that teams often manage separately. Kubernetes engineers think in namespaces, labels, service accounts, and pod security. Cloud engineers think in instance profiles, managed identities, node service accounts, and object storage permissions. Attackers do not respect that split; they only need one path from a compromised workload to credentials with useful cloud permissions.

Hypothetical scenario: a payment API allows a user-supplied URL for image import, and the handler follows redirects from inside the pod. The attacker points the import at the cloud metadata endpoint, receives temporary node-role credentials, and uses those credentials to read an internal bucket that stores deployment manifests. The Kubernetes bug was small, but the blast radius came from overpowered node identity and missing egress policy.

The mental model is a hotel service desk. A guest should ask the desk only for services assigned to their room, but the metadata endpoint is more like an unattended master key drawer in the hallway. NetworkPolicy locks the hallway door for application pods, provider identity features remove unnecessary master keys from that drawer, and node firewall rules add a guardrail if the first lock is missing or bypassed.

---

## The Metadata Attack

```
+--------------------+       HTTP to link-local        +----------------------+
| Compromised pod    | ------------------------------> | Metadata service     |
| app, shell, SSRF   |   169.254.169.254 or provider   | node identity,       |
| vulnerable sidecar |   metadata hostname             | tokens, config       |
+---------+----------+                                 +----------+-----------+
          |                                                       |
          | stolen temporary credentials                          |
          v                                                       v
+--------------------+                                 +----------------------+
| Cloud APIs         | <------------------------------ | IAM / managed        |
| storage, queues,   |        signed requests          | identity permissions |
| secrets, registry  |                                 | attached to node     |
+--------------------+                                 +----------------------+
```

The critical detail is that `169.254.169.254` is not a normal internet destination. It is an IPv4 link-local address, and cloud platforms use it so a VM can ask the local platform for facts about itself without DNS or a routed network path. A pod does not need public internet access to try this address. If the node routes pod traffic toward the host network, the request can still be local enough to matter.

The usual application-layer entry is SSRF, which means the attacker persuades a server-side component to make an HTTP request chosen by the attacker. A container shell is even simpler, but SSRF is the exam-relevant pattern because it appears in ordinary web services. The application thinks it is fetching a thumbnail, webhook, package, or callback URL; the attacker chooses a metadata URL instead.

Once credentials are returned, the attacker stops being limited by Kubernetes verbs. The next step might be `aws s3 ls`, a Google Cloud API call using an access token, or an Azure Managed Identity token request for Key Vault. If the node identity has broad permissions, the pod compromise becomes a cloud compromise even when Kubernetes RBAC was tight.

The defensive lesson is to block the path before you rely on application behavior. Developers can fix SSRF bugs, but platform teams need a baseline where a missed validation bug does not expose node credentials. NetworkPolicy is the Kubernetes control you can actually apply across workload namespaces, but it only works when your CNI enforces egress policy.

There is one more subtlety: metadata exposure is often invisible during normal application tests. A service can pass readiness probes, serve user traffic, and pass RBAC checks while still being able to fetch node credentials. That is why metadata protection belongs in a standard namespace baseline. You should not wait until a specific app team remembers to ask for it.

> **Pause and predict**: A pod has no Kubernetes RBAC permissions beyond reading its own ConfigMap. The node IAM role can read a production object bucket. If the pod can reach metadata, which permission set matters after credentials are stolen: the pod's RBAC role or the node's cloud role?

---

## Metadata Endpoints by Provider

| Cloud Provider | Metadata Endpoint | Credential-Sensitive Path | Important Request Behavior |
|----------------|-------------------|---------------------------|----------------------------|
| AWS EC2 / EKS nodes | `http://169.254.169.254` | [`/latest/meta-data/iam/security-credentials/`](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html) | IMDSv1 accepts simple HTTP GETs when enabled; IMDSv2 requires a session token first. |
| Google Compute Engine / GKE nodes | `http://169.254.169.254` or `http://metadata.google.internal` | [`/computeMetadata/v1/instance/service-accounts/`](https://cloud.google.com/compute/docs/metadata/querying-metadata) | Requests must include `Metadata-Flavor: Google`; recursive listing uses `?recursive=true`. |
| Azure VMs / AKS nodes | `http://169.254.169.254` | [`/metadata/identity/oauth2/token`](https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-service) | Requests must include `Metadata: true` and an `api-version` query parameter. |

All three providers expose the familiar **169.254.169.254** link-local address, but they do not expose exactly the same API. That difference matters during both attack analysis and defensive testing. A failed probe without the provider-required header does not prove the endpoint is protected; it may only prove the request was malformed.

On AWS, the exam focus is the difference between IMDSv1 and IMDSv2. IMDSv1 allows direct unauthenticated GET requests to metadata paths when the instance permits it. IMDSv2 requires a caller to obtain a token with a PUT request to `/latest/api/token`, then present that token on later metadata requests with `X-aws-ec2-metadata-token`.

The IMDSv2 hop limit is a separate defense. AWS lets you configure the number of network hops that the token PUT response may traverse, with a configurable range documented by EC2. A low hop limit can make token retrieval fail from a container network path, but it does not replace pod egress policy because host-network pods and node-level processes have different network placement.

On Google Cloud, the metadata server requires the `Metadata-Flavor: Google` header. Query patterns often use `?recursive=true` to list nested metadata trees, which is exactly why a sloppy SSRF defense is dangerous. If an attacker can add headers and query strings, the metadata API becomes easier to enumerate. GKE also has its own cluster metadata posture, and modern guidance points learners toward Workload Identity Federation for GKE rather than relying on legacy metadata concealment alone.

On Azure, the IMDS endpoint also uses `169.254.169.254`, but the request shape is different. The `Metadata: true` header is required, and token retrieval for managed identity uses `/metadata/identity/oauth2/token` with parameters such as `api-version` and `resource`. The header requirement stops accidental browser-style requests, but it does not stop a pod where the attacker can run `curl`.

This is why the Kubernetes control is intentionally boring: block egress to the link-local metadata address for application workloads. Provider headers and token flows reduce accidental exposure and raise attacker effort. NetworkPolicy removes the route for pods that should never need the endpoint in the first place.

The provider table should also change how you read logs. A failed AWS metadata GET, a GCP metadata request with the correct header, and an Azure managed identity token URL are different signals, but all point toward the same intent: a workload is trying to learn about the node or obtain cloud identity. If your runtime telemetry or egress logs show these patterns from application namespaces, investigate them as credential-access behavior, not as ordinary outbound HTTP.

---

> **Pause and predict**: An attacker compromises an application pod and runs `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/`. They get temporary AWS credentials with S3 read access. What can they do next, and which control would have stopped the first network request?

## Protection Method 1: NetworkPolicy

Block egress to the metadata IP using NetworkPolicy as your first defense layer; in practice, this is often the simplest way to express "pods should not talk to cloud control-plane secrets."

When writing the rule, think of it as narrowing the pod egress surface area, not just adding a deny list. The policy makes intent explicit for every workload and gives you a versioned, reviewable security control that can be tested and rolled back.

NetworkPolicy works by selecting pods and then allowing only matching traffic for the selected direction. There is no portable "deny" action in the Kubernetes NetworkPolicy API. You create denial by isolating selected pods for egress and then writing allow rules that omit the destination you want blocked. For metadata protection, the common pattern is `0.0.0.0/0` with `except: 169.254.169.254/32`.

That `except` field is doing important work. It says "allow all IPv4 destinations covered by this CIDR except the metadata IP." If you instead write only a default deny policy without restoring normal egress, applications may fail for unrelated reasons. If you allow `0.0.0.0/0` without the exception, the policy documents intent but still permits the risky endpoint.

The major caveat is enforcement. Kubernetes accepts NetworkPolicy objects even when the installed CNI plugin does not enforce them. The upstream docs call out that a cluster must use a network plugin that supports NetworkPolicy enforcement. In a CKS answer, always pair the YAML with a runtime probe, because `kubectl get networkpolicy` only proves the object exists.

NetworkPolicy also has a scope boundary that is easy to forget under exam pressure. Policies are namespace-scoped objects, and a `podSelector` selects pods only inside the policy's namespace. Applying a perfect policy to `default` does not protect `production`, and applying it to `production` does not protect `staging`. When the task says "all workload namespaces," repeat the object or use your platform's policy automation to stamp the same baseline everywhere.

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

Read this policy from the bottom up during the exam. The selected pods are every pod in `production`. Egress isolation is enabled because `policyTypes` includes `Egress`. The single egress rule allows destinations in all IPv4 space except one `/32`. Since NetworkPolicies are additive, another policy selecting the same pods could accidentally re-allow metadata if it contains a broader egress allow. Audit the effective policy set, not one file in isolation.

### Allow DNS with Metadata Block

Many exam failures on egress policy are self-inflicted DNS failures. Once a pod is egress-isolated, DNS packets to CoreDNS must be allowed explicitly unless your broader egress rule also covers them. Writing a DNS rule first makes the intent readable and gives you a place to tighten name-resolution access later.

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

The DNS selector shown here is a pattern, not a guarantee for every cluster. Some clusters label CoreDNS as `k8s-app: kube-dns`; others use different labels or NodeLocal DNSCache. In a live exam environment, inspect the `kube-system` pods and labels before copying selectors. A correct policy that selects no DNS pods is still a broken policy.

Host-network workloads need separate attention. Some CNIs do not apply ordinary pod NetworkPolicy to `hostNetwork: true` pods in the same way they apply it to normal pod networking. That matters because privileged agents, CNI components, CSI drivers, and monitoring daemons often run with host networking. Treat those pods as exceptions that need provider-level controls, node firewall rules, and least-privilege identity, not just namespace policy.

From an operations perspective, metadata policy should be owned like any other security baseline. Put it in Git, test it in a disposable namespace, and roll it out with the same process used for default deny, pod security labels, and admission policy. A one-off `kubectl apply` during an incident may be useful, but durable protection comes from making metadata blocking part of namespace creation.

---

## Protection Method 2: iptables on Nodes

Configure iptables rules on each node to block metadata access, and treat these rules as a host-based backstop that catches traffic the CNI policy layer misses:

Node firewalling is defense in depth, not the first control you should reach for in a normal Kubernetes namespace. It is harder to audit through Kubernetes APIs, varies by Linux distribution, and must survive node replacement. Its value is that it can protect paths outside ordinary pod policy, especially host-network workloads, unmanaged node processes, and emergency clusters where the CNI does not enforce egress policy yet.

```bash
# Block metadata access from pods (run on each node)
iptables -A OUTPUT -d 169.254.169.254/32 -j REJECT

# Or more specifically, block forwarded pod traffic from a known pod CIDR
iptables -I FORWARD -s 10.244.0.0/16 -d 169.254.169.254/32 -j REJECT

# Make persistent (varies by OS)
iptables-save > /etc/iptables/rules.v4
```

The distinction between `OUTPUT` and `FORWARD` is worth knowing. `OUTPUT` controls traffic generated by local node processes, while pod traffic may pass through forwarding or CNI-specific chains before it leaves the node namespace. If your CNI uses eBPF or nftables instead of classic iptables chains, the exact hook can differ. That is why node-level rules should be tested on the actual node image and CNI combination, not assumed from a blog snippet.

Use `REJECT` or `DROP` intentionally. `DROP` produces a timeout and looks like a dead endpoint, which may hide a policy failure during debugging. `REJECT` returns an immediate failure and is easier to verify, but it can change application error behavior. For a lab or exam verification, either result is acceptable if you document the expected signal and prove metadata is not returned.

### DaemonSet for iptables Rules

This DaemonSet uses `hostNetwork: true` and `NET_ADMIN` privileges so it can modify the node's actual iptables rules rather than the pod's isolated network namespace. That distinction matters because ordinary pods only control their own networking namespace, which means a `iptables` change inside one pod does not automatically become a node-wide enforcement point. Using a DaemonSet is defensive in depth when you need host-level enforcement, but it also expands your blast radius, so you should combine it with strict pod security and operational guardrails.

Do not treat this DaemonSet as a general production recommendation without review. A privileged DaemonSet that can change host networking is itself a high-value target. If you use this pattern, pin the image, restrict who can update it, run it only in a system namespace, and make the node rule idempotent so repeated restarts do not add duplicate rules.

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
      containers:
      - name: blocker
        image: alpine:3.20
        command:
        - /bin/sh
        - -c
        - |
          apk add iptables
          iptables -C FORWARD -d 169.254.169.254/32 -j REJECT 2>/dev/null || \
          iptables -I FORWARD -d 169.254.169.254/32 -j REJECT
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

The important CKS distinction is that IMDSv2 is not simply "metadata on or off." It has at least two relevant knobs: whether tokens are required, and how many network hops the metadata token response may traverse. Requiring tokens blocks IMDSv1-style one-shot GET requests. A strict hop limit can stop token retrieval from normal pod networks, but it can also break legitimate software in container environments if the workload truly needs metadata.

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

For EKS, pair IMDSv2 with identity isolation for workloads. [IAM Roles for Service Accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) and [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) both let you associate cloud permissions with a Kubernetes service account rather than making pods borrow the node instance profile. This is the cleanest long-term fix: do not mount node IAM into application pods at all.

There is a nuance that exam answers often miss. AWS documents that pods using `hostNetwork: true` will always have IMDS access, although SDKs should use IRSA or Pod Identity credentials when configured. That means IMDS blocking and workload identity are complementary. Workload identity gives the application the right credentials; metadata blocking prevents the same application from falling back to the broader node role.

### GKE Workload Metadata Mode

If workloads move across providers, this is your equivalent to IMDS controls on GCP: configure metadata behavior at the node-pool level so workloads do not assume unrestricted metadata exposure by default. In many environments this starts as a "one flag in pool config" change and becomes a reliable baseline safeguard for all new nodes.

GCP requests need the `Metadata-Flavor: Google` header, and a recursive query can list a tree of metadata under `/computeMetadata/v1/`. That header requirement prevents some accidental reads, but it does not protect against a controlled pod process. A compromised container can add the header as easily as it can run any other HTTP request.

```bash
# Enable the GKE Metadata Server for Workload Identity on the node pool
# (requires Workload Identity enabled on the cluster)
gcloud container node-pools update POOL_NAME \
  --cluster=CLUSTER_NAME \
  --workload-metadata=GKE_METADATA
```

The older `--workload-metadata=SECURE` mode implemented legacy metadata concealment; GKE has deprecated that path in favor of Workload Identity Federation and the `GKE_METADATA` server mode. See [GKE cluster metadata protection](https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata) for the current posture.

Current GKE guidance favors [Workload Identity Federation for GKE](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) for application access to Google Cloud APIs. The design is the same principle as IRSA: bind cloud access to a Kubernetes service account and avoid exposing broad node credentials to arbitrary pods. Node service accounts should also be least privilege, because a metadata protection bypass is far less damaging when the node identity cannot read sensitive project resources.

### Azure Instance Metadata Service (IMDS)

Azure requires specific headers, and the endpoint accepts only calls that include those security markers, which is why simple unauthenticated probes often fail even when the IP is reachable.

In a Kubernetes threat model, this means your defenses should still assume a determined attacker may test multiple metadata flavors and chains, because headers can be learned but not always trusted if the pod is already running with privileged network access.

```bash
# Azure IMDS requires Metadata header; instance probe omits resource=
curl -H "Metadata:true" \
  "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
```

A managed-identity token URL without `resource=` may return HTTP 400 even when IMDS is reachable. Use that token path only when you need a real credential test, not as a simple reachability probe.

On AKS, prefer [Microsoft Entra Workload ID](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview) for application pods that need Azure resources. It uses Kubernetes service account tokens and OIDC federation so the workload can exchange its projected identity for Azure credentials. That is safer than giving every pod a path to the node's managed identity and then hoping application bugs never reach IMDS.

Across providers, the pattern is consistent: provider metadata features reduce the power of the endpoint, and Kubernetes egress policy reduces reachability to it. Least-privilege node roles reduce blast radius if a bypass still occurs. Workload identity reduces the reason for pods to touch node metadata at all.

This identity-first angle is the difference between "blocked today" and "safe by design." If a pod genuinely needs cloud access, give it a narrowly scoped workload identity and prove the application can use that path. If it does not need cloud access, metadata should be unreachable. If the only working credential path is the node role, the cluster is still depending on shared infrastructure identity in a place where workloads should be isolated.

---

## Testing Metadata Access

### Verify Pod Can't Access Metadata

Use this check early in your validation flow to confirm the policy is active for a test pod in the target namespace. If metadata is blocked, your probe should fail or timeout; that behavior is the expected security signal, not a platform error.

Always run the probe from a pod selected by the policy. Testing from your laptop, from a node shell, or from a pod in another namespace tells you almost nothing about the workload you meant to protect. The most useful test names the namespace, uses a short timeout, and prints an explicit message for both outcomes.

```bash
# Create test pod
kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- \
  curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/

# Expected: Connection timeout or refused
# If you see instance metadata, protection isn't working!
```

When you test provider-specific behavior, use the provider's real request shape. On AWS IMDSv2, a plain GET may fail because a token is required, while a PUT token request could still succeed. On GCP and Azure, missing headers can create false confidence. A good validation plan has both a simple reachability probe and a provider-shaped probe.

```bash
# AWS IMDSv2 token probe: this should fail from ordinary application pods
kubectl run aws-token-probe --image=curlimages/curl --rm -i --restart=Never -- \
  curl -sS --connect-timeout 2 -X PUT \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 60" \
  http://169.254.169.254/latest/api/token

# GCP-shaped probe: this should fail from ordinary application pods
kubectl run gcp-metadata-probe --image=curlimages/curl --rm -i --restart=Never -- \
  curl -sS --connect-timeout 2 \
  -H "Metadata-Flavor: Google" \
  "http://169.254.169.254/computeMetadata/v1/?recursive=true"
```

In a local kind cluster there is normally no real cloud metadata service, so the before probe may already time out. That is still useful for practicing the command sequence, but it does not prove cloud enforcement. The proof in kind is that a NetworkPolicy-enforcing CNI is installed, the policy selects the pod, normal egress still works, and the metadata probe fails consistently.

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

Do one more check for accidental re-allow rules. NetworkPolicies combine additively, so another egress policy can allow traffic even when your metadata policy looks correct by itself. In small exam clusters, `kubectl get networkpolicy -A` is quick enough to review manually. In production, export policies and review them with policy-as-code tests.

When a test fails, debug in layers. First confirm the probe pod is in the intended namespace and has labels selected by the policy. Then confirm the CNI enforces NetworkPolicy. Next inspect other policies that select the same pod. Finally, test provider-shaped requests so you do not mistake a malformed metadata request for a blocked path.

---

## Complete Security Example

The following example pulls together egress policy behavior used in production patterns: allow internal service communication, permit DNS, and explicitly exclude metadata from the broader egress set. This shape is useful because it preserves day-to-day connectivity while keeping the risk-bearing link-local endpoint unreachable.

Treat this as a namespace baseline for ordinary application workloads, not as a cluster-wide copy-paste object. System namespaces may need controlled metadata access for node bootstrap, cloud controllers, CSI drivers, or provider agents. Application namespaces usually do not. The secure default is to apply this shape to workload namespaces and create narrow exceptions only when an owner can explain the need.

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
        - 169.254.169.254/32
```

Avoid broad link-local blocking unless you have mapped all provider-specific agents. For example, EKS Pod Identity uses a different link-local endpoint for the Pod Identity Agent, and other CNIs or node-local services may use link-local space for legitimate cluster plumbing. The CKS-friendly answer is the precise metadata `/32`; broader ranges belong in a design review, not in an exam sprint.

The security example still needs identity work. If the node role has administrator-style permissions, blocking metadata lowers exposure but does not fix the underlying blast radius. Use least-privilege node roles for kubelet and node add-ons, then bind application cloud permissions through IRSA, EKS Pod Identity, Workload Identity Federation for GKE, or Microsoft Entra Workload ID. That way a single bypass does not inherit the whole node's cloud authority.

For production rollout, start with observe mode in a non-critical namespace. Create a disposable pod, test DNS, test required external destinations, test metadata, and record the expected outputs. Then apply the same baseline to a real workload namespace during a maintenance window or through progressive delivery. Metadata blocking is usually low risk for application pods, but egress isolation can reveal hidden dependencies that deserve a controlled rollout.

Keep exception handling boring and explicit. If one workload claims it needs metadata, ask which API it calls, which credentials it expects, and why workload identity cannot satisfy the same need. Most exceptions shrink after that conversation. The remaining ones should be labeled, owned, and tested because they are now part of the cluster's trusted computing base.

---

## Real Exam Scenarios

### Scenario 1: Block Metadata Access for Namespace

This is the pattern examiners often probe: can you apply a policy with minimal overreach and still keep behavior predictable. The snippet is intentionally namespace-scoped so you practice control-plane granularity without touching system components.

Read the task wording carefully. If it says "all pods in namespace `production`," use `podSelector: {}` in that namespace. If it says "pods labeled `tier=frontend`," do not accidentally isolate every workload. CKS rewards precision because broad policies can break unrelated pods and narrow policies can leave the vulnerable pod exposed.

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

Once a policy is in place, always verify with an explicit failure expectation so operators reading your remediation can tell protected and unprotected paths apart. Use an exit-coded check during remediation checks to avoid false-positive "looks fine" interpretations during incident review and exam grading.

The fastest exam-safe verification is a short-timeout curl pod with a clear fallback message. Do not wait for a long TCP timeout. Do not use a running application pod unless the task asks you to avoid creating a test pod. A disposable probe is easy to clean up and leaves less state behind.

```bash
# Create test pod
kubectl run metadata-test --image=curlimages/curl -n production --rm -i --restart=Never -- \
  curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/ || echo "BLOCKED (expected)"
```

### Scenario 3: Allow Specific Pod Access

Not every workload should be blocked; this scenario demonstrates an explicit exception pattern. You can constrain that exception to monitoring or agent pods while still preserving broad protections for untrusted workloads.

This should be rare. In modern clusters, a monitoring agent that needs cloud APIs should normally use a workload identity binding rather than reading the node metadata service. If you still need an exception, isolate it by namespace and label, require a named owner, and include a verification command that proves only the selected pods can reach the endpoint.

The exam may present the exception as a legitimate agent because it wants to see whether you can avoid breaking cluster operations. The professional version of the same answer is more skeptical. Allow the agent only if the requirement is documented, the label cannot be copied by arbitrary users, and the cloud permissions behind that path are narrower than the node's default role.

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

The exception policy above is intentionally blunt so you can see the shape. In production, combine it with narrower ports, workload identity, and admission controls that prevent random pods from copying the `app: cloud-monitor` label. Labels are not a security boundary unless admission policy controls who can set them.

---

> **Pause and predict**: You block metadata access for the `production` namespace with a NetworkPolicy. But you don't apply it to `kube-system`. Why might this be intentional, and what risk does it introduce?

## Defense in Depth

Single controls are useful, but defenses fail from edge cases more often than from one missing line of docs. Build in layers: kube-network policy, provider-level metadata posture, node-level enforcement, and runtime least-privilege, then validate each layer independently.

```
+------------------------------------------------------------------+
| Metadata protection layers                                       |
+------------------------------------------------------------------+
| 1. Workload identity: give pods their own least-privilege role    |
| 2. NetworkPolicy: block app-pod egress to 169.254.169.254/32      |
| 3. Provider posture: require IMDSv2 or provider metadata controls |
| 4. Node firewall: block unexpected host and forwarded paths       |
| 5. Pod security: limit hostNetwork, privileged pods, NET_ADMIN    |
| 6. Audit: probe after changes and review cloud credential use     |
+------------------------------------------------------------------+
```

The ordering is deliberate. Workload identity reduces dependence on node credentials before you start tuning network paths. NetworkPolicy removes the route for ordinary pods. Provider controls make metadata harder to abuse if a route remains. Node firewalling covers awkward host paths. Pod security reduces the number of workloads that can bypass normal pod networking.

Auditing closes the loop. Look for pods using `hostNetwork: true`, pods with `NET_ADMIN`, privileged DaemonSets, namespaces without egress policy, and node roles with broad storage or secrets access. A cluster can pass a simple curl test and still be risky if one privileged agent runs arbitrary user workloads or if node credentials remain overpowered.

Finally, watch cloud logs. AWS CloudTrail, Google Cloud audit logs, and Azure activity logs can reveal unexpected use of node identities. If application teams should be using workload identity, a sudden spike in node-role API calls from an application path is a signal to investigate both identity configuration and metadata reachability.

Admission policy is another useful supporting layer. You can restrict `hostNetwork`, privileged containers, and `NET_ADMIN` so application teams cannot accidentally create pods that bypass the normal network path. That does not directly block metadata, but it reduces the set of workloads that need special review and keeps the NetworkPolicy model easier to reason about.

The final layer is documentation for exceptions. Every namespace or workload that can reach metadata should have an owner, a reason, and a replacement plan if workload identity can remove the need. Undocumented exceptions are where drift becomes exposure: six months later, nobody remembers why a pod needed node credentials, but the path still exists.

---

## Did You Know?

- **[169.254.0.0/16 is link-local.](https://www.rfc-editor.org/rfc/rfc3927)** It is reserved for local network communication rather than internet routing. Cloud providers use this property for metadata because an instance can reach the platform service without depending on DNS, public routes, or a customer-managed gateway.

- **A NetworkPolicy object can be present and still do nothing.** [Kubernetes requires a network plugin that supports NetworkPolicy enforcement](https://kubernetes.io/docs/concepts/services-networking/network-policies/). That is why a verifier should include a runtime probe from a selected pod, not only a YAML review.

- **Metadata headers are not authorization.** GCP requires `Metadata-Flavor: Google`, and Azure requires `Metadata: true`, but an attacker with code execution inside a pod can add those headers. Treat provider headers as request-shape controls, not as a substitute for identity and network isolation.

- **Blocking all link-local traffic can be too broad.** AWS EKS Pod Identity uses a link-local endpoint that is different from the EC2 metadata IP. Blocking `169.254.169.254/32` targets the node metadata service precisely; blocking the whole `169.254.0.0/16` range needs provider-agent review.

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Applying a policy but never testing from a selected pod | The object can exist even when the CNI does not enforce NetworkPolicy or the podSelector matches nothing. | Run a short-timeout curl probe from the exact namespace and labels covered by the policy. |
| Forgetting DNS after enabling egress isolation | Pods fail with name-resolution errors, and the metadata fix gets blamed for unrelated outages. | Add explicit TCP and UDP port 53 egress to the actual CoreDNS or NodeLocal DNS targets. |
| Blocking `kube-system` with the same workload policy | Cloud controllers, CSI drivers, node agents, or provider add-ons may legitimately need metadata-like paths. | Scope baseline metadata blocking to application namespaces and design system exceptions separately. |
| Assuming IMDSv2 makes NetworkPolicy unnecessary | Host-network pods, node processes, provider differences, and configuration drift can still expose metadata paths. | Require IMDSv2 where available and still block metadata egress for ordinary workload pods. |
| Using `169.254.0.0/16` without reviewing provider agents | Broad link-local blocks can break EKS Pod Identity, NodeLocal DNS, or other node-local services. | Start with `169.254.169.254/32`; broaden only after mapping legitimate link-local dependencies. |
| Giving every workload the node's cloud permissions | A single SSRF or shell escape can inherit the node role and reach unrelated cloud resources. | Use IRSA, EKS Pod Identity, Workload Identity Federation for GKE, or Microsoft Entra Workload ID. |
| Treating labels as a secure exception boundary | A user who can set labels may copy the metadata-allowed label onto an unauthorized pod. | Protect exception labels with admission policy and narrow RBAC for workload updates. |
| Testing only a plain GET request | Provider controls can reject malformed requests while a correctly shaped token request still works. | Test AWS token PUT, GCP `Metadata-Flavor: Google`, and Azure `Metadata: true` paths when relevant. |

---

## Quiz

1. **A penetration tester gets a shell in an application pod and runs `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/node-role`. The response contains temporary AWS credentials. What failed, and what two changes would you make first?**
   <details>
   <summary>Answer</summary>
   The pod could reach the node metadata service, and the node role had useful permissions. First, apply an egress NetworkPolicy to the workload namespace that allows normal destinations except `169.254.169.254/32`, then verify with a pod selected by the policy. Second, enforce IMDSv2 on the node group and move application permissions to IRSA or EKS Pod Identity so the pod does not need the node role. The network fix blocks the route; the identity fix reduces blast radius.
   </details>

2. **A teammate applies the metadata-blocking policy to every namespace, including `kube-system`. A cloud controller starts failing. Should you remove all metadata protection or create an exception?**
   <details>
   <summary>Answer</summary>
   Create a scoped exception or remove the workload policy from system namespaces, but keep metadata protection for application namespaces. System components such as cloud controllers, autoscalers, provider agents, and CSI drivers can have legitimate metadata dependencies. The safer design is namespace-specific policy for user workloads, provider controls on nodes, least-privilege node roles, and separate review for system components.
   </details>

3. **Your AWS nodes require IMDSv2 and use a hop limit of 1. A reviewer says metadata NetworkPolicies are redundant. Is that correct for all pods?**
   <details>
   <summary>Answer</summary>
   No. IMDSv2 reduces risk, but it is an AWS-specific provider control and does not replace Kubernetes egress policy. Host-network pods and node processes have different network placement, and configuration drift can weaken metadata options on future nodes. Keep NetworkPolicy for ordinary workload namespaces, enforce IMDSv2 at the provider layer, and audit `hostNetwork: true` pods separately.
   </details>

4. **A GKE pod cannot access `http://169.254.169.254/computeMetadata/v1/` with a plain GET. Your teammate concludes metadata is protected. What extra test should you run?**
   <details>
   <summary>Answer</summary>
   Run a provider-shaped request with `Metadata-Flavor: Google`, and include `?recursive=true` if you are checking whether metadata trees can be listed. A plain GET can fail because the required header is missing, not because the network path is blocked. The reliable signal is a timeout or connection failure from a selected pod when the request includes the correct provider header.
   </details>

5. **You write an egress NetworkPolicy with only a DNS allow rule. Metadata is blocked, but the application cannot reach its external API. What did the policy do?**
   <details>
   <summary>Answer</summary>
   The selected pods became egress-isolated, and only DNS traffic matched an allow rule. NetworkPolicy does not start from "allow everything except my deny"; it starts allowing only the traffic you explicitly describe once isolation applies. Add a second egress rule that allows the required destinations, such as `0.0.0.0/0` with `except: 169.254.169.254/32`, or a narrower CIDR set if the application has fixed destinations.
   </details>

6. **A security team blocks `169.254.0.0/16` for every pod. After migration to EKS Pod Identity, some workloads cannot obtain credentials from the Pod Identity Agent. What likely happened?**
   <details>
   <summary>Answer</summary>
   The policy was broader than the EC2 metadata endpoint. EKS Pod Identity uses a link-local address that is not `169.254.169.254`, so a blanket link-local block can break legitimate provider identity plumbing. Use the precise metadata `/32` for the node metadata service unless you have mapped every legitimate link-local dependency and created explicit exceptions.
   </details>

7. **A workload namespace has the correct metadata-blocking policy, but one privileged DaemonSet with `hostNetwork: true` can still reach metadata. Is the NetworkPolicy broken?**
   <details>
   <summary>Answer</summary>
   Not necessarily. Host-network pods often sit outside the ordinary pod network path that NetworkPolicy protects, depending on the CNI and implementation. Treat that DaemonSet as a separate high-risk workload: remove host networking if possible, bind it to a least-privilege workload identity, restrict who can update it, and consider node-level firewall rules for host paths.
   </details>

---

## Hands-On Exercise

**Task**: Block metadata access and verify protection on a kind v1.35 cluster. Treat it as a controlled exercise: first observe current behavior, then apply your policy changes, then run post-change probes so the security state is reproducible for future audits.

### Prerequisites

- [ ] You have a Kubernetes v1.35 kind cluster available, and you can create disposable namespaces without affecting any shared environment.
- [ ] Ensure your kind cluster enforces NetworkPolicy (default kind v0.24+ kindnet does; older clusters may need Calico/Cilium).
- [ ] `kubectl` points at the test cluster, and `kubectl config current-context` shows the disposable context you intend to use.
- [ ] You understand that kind has no real cloud IMDS, so the before probe may fail because the endpoint is absent.

### Step 1: Create a workload namespace and prove normal egress works

```bash
# Setup namespace
kubectl create namespace metadata-test

# External egress should work before protection
kubectl run external-before \
  --image=curlimages/curl \
  -n metadata-test \
  --rm -i --restart=Never -- \
  curl -sS --connect-timeout 5 https://kubernetes.io -o /dev/null -w "HTTP %{http_code}\n"
```

- [ ] The namespace exists, and you can list it with `kubectl get namespace metadata-test` before creating any policy.
- [ ] The external egress probe returns an HTTP status code, which proves ordinary outbound traffic works before isolation.

### Step 2: Run the metadata probe before applying the policy

```bash
# In kind this usually prints METADATA_BLOCKED_OR_ABSENT because there is no cloud IMDS.
# In a real cloud cluster this might return metadata if protection is missing.
kubectl run metadata-before \
  --image=curlimages/curl \
  -n metadata-test \
  --rm -i --restart=Never -- \
  sh -c 'curl -sS --connect-timeout 3 http://169.254.169.254/latest/meta-data/ || echo METADATA_BLOCKED_OR_ABSENT'
```

- [ ] In kind, the command finishes without returning cloud metadata, which is expected because no real IMDS exists locally.
- [ ] In a real cloud cluster, any returned metadata is treated as a finding and should trigger immediate policy review.

### Step 3: Apply a NetworkPolicy that allows normal egress except IMDS

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-node-metadata
  namespace: metadata-test
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
EOF
```

- [ ] The policy applies without validation errors, and `kubectl get networkpolicy -n metadata-test` lists the new object.
- [ ] The policy uses `169.254.169.254/32`, not a blanket link-local range that might break provider agents.

### Step 4: Verify the policy object and selected namespace

```bash
kubectl get networkpolicy -n metadata-test
kubectl describe networkpolicy block-node-metadata -n metadata-test
kubectl get namespace metadata-test --show-labels
```

- [ ] `block-node-metadata` appears in the `metadata-test` namespace, which confirms the object landed in the intended scope.
- [ ] The egress rule shows both DNS allowances and the `ipBlock` exception, which confirms the policy preserves normal name resolution.

### Step 5: Probe after the policy

```bash
kubectl run metadata-after \
  --image=curlimages/curl \
  -n metadata-test \
  --rm -i --restart=Never -- \
  sh -c 'curl -sS --connect-timeout 3 http://169.254.169.254/latest/meta-data/ || echo METADATA_BLOCKED_OR_ABSENT'

kubectl run external-after \
  --image=curlimages/curl \
  -n metadata-test \
  --rm -i --restart=Never -- \
  curl -sS --connect-timeout 5 https://kubernetes.io -o /dev/null -w "HTTP %{http_code}\n"
```

- [ ] The metadata probe does not return metadata, and the result is documented as either blocked by policy or absent in kind.
- [ ] The external egress probe still returns an HTTP status code, proving that the policy did not accidentally create a broad outage.
- [ ] If metadata succeeds after the policy, confirm that your CNI enforces NetworkPolicy and that no other policy re-allows the destination.

### Step 6: Cloud-only illustrative validation

These checks are illustrative because kind does not provide AWS, GCP, or Azure metadata. Run them only in an authorized cloud test cluster where you understand the impact.

```bash
# AWS IMDSv2 token request: should fail from ordinary application pods
kubectl run aws-imdsv2-after \
  --image=curlimages/curl \
  -n metadata-test \
  --rm -i --restart=Never -- \
  sh -c 'curl -sS --connect-timeout 3 -X PUT \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 60" \
    http://169.254.169.254/latest/api/token || echo AWS_TOKEN_BLOCKED'

# GCP metadata request: should fail from ordinary application pods
kubectl run gcp-metadata-after \
  --image=curlimages/curl \
  -n metadata-test \
  --rm -i --restart=Never -- \
  sh -c 'curl -sS --connect-timeout 3 \
    -H "Metadata-Flavor: Google" \
    "http://169.254.169.254/computeMetadata/v1/?recursive=true" || echo GCP_METADATA_BLOCKED'
```

- [ ] Cloud-shaped metadata requests fail from ordinary workload pods, including requests that use the provider-required headers or token method.
- [ ] Any pod that legitimately needs cloud access uses workload identity rather than node metadata, and the binding is least privilege.

```bash
# Cleanup
kubectl delete namespace metadata-test
```

### Success Criteria

Metadata IP is blocked or absent, external access still works, and the policy is enforced by a CNI that supports egress NetworkPolicy. A successful outcome is a clear pass/fail signal: metadata endpoints are unreachable from the test workload, while general outbound traffic still succeeds.

---

## Summary

**Metadata Service Risk**: Metadata endpoints can leak IAM credentials, node identity, and configuration context; when left open, they are a direct bridge from pod compromise to cloud-resource actions. The module's attack examples are a reminder that metadata abuse should be handled as a practical risk, not an abstract cloud-hardening topic.

**Protection Methods**: This module combines four defensive layers: NetworkPolicy egress restrictions, cloud-provider IMDS enforcement, host-level iptables enforcement via Kubernetes-native workflows, and pod architecture choices such as avoiding unnecessary `hostNetwork` privileges.

**Best Practices**: Apply defenses to workload namespaces by default, keep DNS egress explicitly allowed, and use layered controls so one control failure does not expose metadata. Regularly run the validation probes after drift events, because control posture is only reliable when proven in repeatable checks.

These points are only safe when backed by repeatable checks: if you cannot observe blocked/allowed behavior on demand, you should treat the control as incomplete even if the intent is documented.

**Exam Tips**: Focus on writing NetworkPolicies cleanly from memory, including `ipBlock` exceptions and DNS allowances, and remember that metadata attack prevention is a defense-in-depth objective, not a single toggle.

The shortest safe answer is still layered. Block `169.254.169.254/32` for ordinary workload pods, verify that the selected pod cannot reach the endpoint, require provider metadata hardening on nodes, and move application cloud permissions onto workload identity. If one of those layers is missing, call out the residual risk instead of pretending the cluster is fully protected.

When time is short, prioritize the control the exam can observe. Write the NetworkPolicy, run the probe, and state the CNI caveat. If the task includes provider configuration, add IMDSv2, GKE workload metadata posture, or Azure workload identity as requested. If the task asks for a design recommendation, lead with workload identity because it removes the need for application pods to use node metadata at all.

The habit to keep after the exam is simple: every new workload namespace should answer three questions before production traffic arrives. Can ordinary pods reach node metadata? Which identity do they use for cloud APIs? Who owns the exception if the answer is intentionally unusual in production?

---

## Learner check

> NetworkPolicy is the Kubernetes control you can actually apply across workload namespaces, but it only works when your CNI enforces egress policy.

Use that sentence as a quick self-test. If you can explain why both halves matter, you understand the core of this module: Kubernetes accepts the policy object, but real protection comes from enforcement plus a probe from the selected workload.

---

## Next Module

[Module 1.5: GUI Security](../module-1.5-gui-security/) - Securing Kubernetes Dashboard and web UIs.

This transition is intentional: once you have metadata and workload egress under control, you can apply the same threat-model discipline to user-facing administrative surfaces.

## Sources

- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/) - Official NetworkPolicy behavior, including the requirement for an enforcing network plugin.
- [AWS EC2 instance metadata](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html) - Official EC2 metadata categories, including instance identity and IAM role credential paths.
- [AWS IMDSv2 session tokens](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) - Official flow for retrieving and using IMDSv2 tokens.
- [AWS instance metadata options](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html) - Official metadata options, including token requirements and hop limit settings.
- [AWS limiting metadata access](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-metadata-limiting-access.html) - Official AWS guidance on limiting access to instance metadata.
- [Amazon EKS IAM roles for service accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) - Official IRSA guidance for binding AWS permissions to Kubernetes service accounts.
- [Amazon EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) - Official EKS Pod Identity guidance for workload-scoped AWS credentials.
- [Google Compute Engine metadata queries](https://cloud.google.com/compute/docs/metadata/querying-metadata) - Official GCP metadata endpoint, header, and recursive query behavior.
- [GKE cluster metadata protection](https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata) - Official GKE guidance on protecting cluster metadata.
- [Workload Identity Federation for GKE](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) - Official GKE workload identity guidance.
- [Azure Instance Metadata Service](https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-service) - Official Azure IMDS endpoint, headers, and managed identity token path.
- [AKS workload identity overview](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview) - Official AKS guidance for Microsoft Entra Workload ID.
- [RFC 3927 IPv4 link-local addressing](https://www.rfc-editor.org/rfc/rfc3927) - Authoritative reference for the `169.254.0.0/16` link-local range.
